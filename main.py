import os, hmac, hashlib, json, time, base64, asyncio
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler

ROOT=Path(__file__).parent
SUPABASE_URL=os.getenv("SUPABASE_URL","").rstrip("/")
SUPABASE_KEY=os.getenv("SUPABASE_KEY","")
SUPABASE_BUCKET=os.getenv("SUPABASE_BUCKET","generated-images")
BOT_TOKEN=os.getenv("BOT_TOKEN","")
ADMIN_ID=int(os.getenv("ADMIN_ID","0"))
WEBAPP_URL=os.getenv("WEBAPP_URL","").rstrip("/")
API_BASE=os.getenv("API_BASE","https://tooken.club/v1").rstrip("/")
API_KEY=os.getenv("API_KEY","")
IMAGE_MODEL=os.getenv("IMAGE_MODEL","gpt-image-2")
MODERATION_MODEL=os.getenv("MODERATION_MODEL","deepseek-v4-flash")
START_BALANCE=int(os.getenv("START_BALANCE","1"))
IMAGE_COST=int(os.getenv("IMAGE_COST","1"))
MAX_CONCURRENT=int(os.getenv("MAX_CONCURRENT","8"))
TIMEOUT=int(os.getenv("GENERATION_TIMEOUT","180"))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
sem=asyncio.Semaphore(MAX_CONCURRENT)
app=FastAPI(title="ImagesGPT")

app.mount("/static",StaticFiles(directory=str(ROOT/"webapp")),name="static")

def now(): return datetime.now(timezone.utc).isoformat()

def ensure(uid,username="",name=""):
    r=sb.table("users").select("*").eq("user_id",uid).maybe_single().execute()
    if not r.data:
        row={"user_id":uid,"username":username,"full_name":name,
             "balance":START_BALANCE,"created_at":now(),"last_seen":now()}
        sb.table("users").insert(row).execute()
        return row
    sb.table("users").update({
        "username":username,"full_name":name,"last_seen":now()
    }).eq("user_id",uid).execute()
    r=sb.table("users").select("*").eq("user_id",uid).single().execute()
    return r.data

def balance(uid,delta):
    # Balance mutations should ideally be converted to a Postgres RPC
    # for strict atomicity. This function is replaced below by RPC calls.
    r=sb.rpc("change_user_balance",{"p_user_id":uid,"p_delta":delta}).execute()
    return r.data

def reserve(uid):
    r=sb.rpc("reserve_user_coin",{
        "p_user_id":uid,"p_cost":IMAGE_COST
    }).execute()
    return bool(r.data)

def addhist(uid,prompt,size,status,url=None):
    r=sb.table("history").insert({
        "user_id":uid,"prompt":prompt,"size":size,
        "status":status,"image_url":url,"created_at":now()
    }).execute()
    return r.data[0]["id"]

def upd(i,status,url=None):
    sb.table("history").update({
        "status":status,"image_url":url
    }).eq("id",i).execute()

def init_db():
    # Schema is created in supabase/schema.sql.
    # This function intentionally does not create local tables.
    return

class GenReq(BaseModel):
    prompt:str
    size:str="1024x1024"

async def moderate(prompt):
    if not API_KEY: return True
    payload={"model":MODERATION_MODEL,"messages":[{"role":"user","content":"Reply only ALLOW or BLOCK. Block disallowed sexual content, sexual content involving minors, graphic gore, or serious wrongdoing instructions. Prompt: "+prompt}],"temperature":0}
    try:
        async with httpx.AsyncClient(timeout=45) as x:
            r=await x.post(API_BASE+"/chat/completions",headers={"Authorization":"Bearer "+API_KEY},json=payload)
            return r.is_success and r.json()["choices"][0]["message"]["content"].strip().upper().startswith("ALLOW")
    except: return False

async def make_image(prompt,size):
    payload={"model":IMAGE_MODEL,"prompt":prompt,"size":size,"n":1}
    async with sem:
        async with httpx.AsyncClient(timeout=TIMEOUT) as x:
            r=await x.post(API_BASE+"/images/generations",headers={"Authorization":"Bearer "+API_KEY,"Content-Type":"application/json"},json=payload)
            r.raise_for_status(); item=r.json()["data"][0]
    if item.get("url"): return item["url"]
    if item.get("b64_json"):
        raw=base64.b64decode(item["b64_json"])
        name=f"{int(time.time()*1000)}_{hashlib.sha256(raw).hexdigest()[:12]}.png"
        sb.storage.from_(SUPABASE_BUCKET).upload(
            name, raw, {"content-type":"image/png", "upsert":"false"}
        )
        public = sb.storage.from_(SUPABASE_BUCKET).get_public_url(name)
        return public
    raise RuntimeError("No image returned")

@app.get("/")
async def root(): return FileResponse(ROOT/"webapp/index.html")
@app.get("/health")
async def health(): return {"ok":True}

@app.get("/api/me")
async def me(x_telegram_init_data: str|None=Header(default=None)):
    u=await current(x_telegram_init_data)
    r=sb.table("history").select("id",count="exact").eq("user_id",u["user_id"]).eq("status","done").execute()
    n=r.count or 0
    return {"user":{**{k:u[k] for k in ("user_id","username","full_name","balance","created_at")},
                    "id":u["user_id"],"total_images":n}}

@app.get("/api/history")
async def history(x_telegram_init_data: str|None=Header(default=None)):
    u=await current(x_telegram_init_data)
    r=sb.table("history").select("id,prompt,size,status,image_url,created_at").eq("user_id",u["user_id"]).order("id",desc=True).limit(30).execute()
    return {"items":r.data or []}

@app.post("/api/generate")
async def generate(q:GenReq,x_telegram_init_data: str|None=Header(default=None)):
    u=await current(x_telegram_init_data); prompt=q.prompt.strip()
    size=q.size if q.size in {"1024x1024","1536x1024","1024x1536"} else "1024x1024"
    if not prompt: raise HTTPException(400,"Введите описание")
    if len(prompt)>2000: raise HTTPException(400,"Промпт слишком длинный")
    if u["balance"]<IMAGE_COST: raise HTTPException(402,"Недостаточно монет")
    if not await moderate(prompt): raise HTTPException(400,"Запрос не прошёл модерацию")
    if not reserve(u["user_id"]): raise HTTPException(402,"Недостаточно монет")
    hid=addhist(u["user_id"],prompt,size,"processing")
    try:
        url=await make_image(prompt,size); upd(hid,"done",url)
        fresh=ensure(u["user_id"],u["username"],u["full_name"])
        return {"ok":True,"image_url":url,"balance":fresh["balance"]}
    except Exception as e:
        balance(u["user_id"],IMAGE_COST); upd(hid,"error")
        raise HTTPException(502,"Генерация не удалась: "+str(e)[:250])

async def start(update:Update,context):
    if not WEBAPP_URL: await update.message.reply_text("WEBAPP_URL не настроен."); return
    kb=[[InlineKeyboardButton("🖼 Открыть ImagesGPT",web_app=WebAppInfo(url=WEBAPP_URL))]]
    await update.message.reply_text("🤖 ImagesGPT\n\nСоздавай изображения прямо в Telegram.",reply_markup=InlineKeyboardMarkup(kb))

async def addbalance(update:Update,context):
    if update.effective_user.id!=ADMIN_ID or len(context.args)!=2:return
    uid,amount=int(context.args[0]),int(context.args[1]); ensure(uid); await update.message.reply_text(f"Баланс: {balance(uid,amount)}")

async def start_bot():
    b=Application.builder().token(BOT_TOKEN).build()
    b.add_handler(CommandHandler("start",start)); b.add_handler(CommandHandler("addbalance",addbalance))
    await b.initialize(); await b.start(); await b.updater.start_polling(); return b

@app.on_event("startup")
async def startup():
    init_db(); app.state.bot=await start_bot()
@app.on_event("shutdown")
async def shutdown():
    b=getattr(app.state,"bot",None)
    if b:
        await b.updater.stop(); await b.stop(); await b.shutdown()

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","10000")))
