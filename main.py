import os
import hmac
import hashlib
import json
import time
import base64
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import parse_qsl
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client, Client

ROOT = Path(__file__).parent

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "generated-images")

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "").rstrip("/")

API_BASE = os.getenv("API_BASE", "https://tooken.club/v1").rstrip("/")
API_KEY = os.getenv("API_KEY", "")

IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-2")
MODERATION_MODEL = os.getenv("MODERATION_MODEL", "deepseek-v4-flash")
START_BALANCE = int(os.getenv("START_BALANCE", "3"))
IMAGE_COST = int(os.getenv("IMAGE_COST", "1"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "8"))
TIMEOUT = int(os.getenv("GENERATION_TIMEOUT", "180"))

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is required")
if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY is required")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")

sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
sem = asyncio.Semaphore(MAX_CONCURRENT)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="ImagesGPT", lifespan=lifespan)

WEBAPP_DIR = ROOT / "webapp"
if WEBAPP_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEBAPP_DIR)), name="static")

def now():
    return datetime.now(timezone.utc).isoformat()

def ensure(uid, username="", name=""):
    result = sb.table("users").select("*").eq("user_id", uid).maybe_single().execute()
    if not result.data:
        row = {
            "user_id": uid,
            "username": username or "",
            "full_name": name or "",
            "balance": START_BALANCE,
            "created_at": now(),
            "last_seen": now(),
        }
        sb.table("users").insert(row).execute()
        return row
    sb.table("users").update({
        "username": username or "",
        "full_name": name or "",
        "last_seen": now(),
    }).eq("user_id", uid).execute()
    result = sb.table("users").select("*").eq("user_id", uid).single().execute()
    return result.data

def balance(uid, delta):
    result = sb.rpc("change_user_balance", {"p_user_id": uid, "p_delta": delta}).execute()
    return result.data

def reserve(uid):
    result = sb.rpc("reserve_user_coin", {"p_user_id": uid, "p_cost": IMAGE_COST}).execute()
    return bool(result.data)

def addhist(uid, prompt, size, status, url=None):
    result = sb.table("history").insert({
        "user_id": uid,
        "prompt": prompt,
        "size": size,
        "status": status,
        "image_url": url,
        "created_at": now(),
    }).execute()
    return result.data[0]["id"]

def upd(history_id, status, url=None):
    sb.table("history").update({"status": status, "image_url": url}).eq("id", history_id).execute()

def validate_telegram_init_data(init_data):
    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram initData is missing")
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.get("hash")
    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram hash is missing")
    data_check_string = "\n".join(f"{key}={parsed[key]}" for key in sorted(parsed) if key != "hash")
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData")
    try:
        telegram_user = json.loads(parsed["user"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Telegram user data")
    uid = telegram_user.get("id")
    if not uid:
        raise HTTPException(status_code=401, detail="Telegram user ID is missing")
    first = telegram_user.get("first_name", "")
    last = telegram_user.get("last_name", "")
    return {"user_id": int(uid), "username": telegram_user.get("username", ""), "full_name": f"{first} {last}".strip()}

def current_sync(init_data):
    u = validate_telegram_init_data(init_data)
    return ensure(u["user_id"], u["username"], u["full_name"])

async def moderate(prompt):
    if not API_KEY:
        return True
    payload = {
        "model": MODERATION_MODEL,
        "messages": [{"role": "user", "content": "Reply only ALLOW or BLOCK. Block disallowed sexual content, sexual content involving minors, graphic gore, or serious wrongdoing instructions.\n\nPrompt: " + prompt}],
        "temperature": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(API_BASE + "/chat/completions", headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}, json=payload)
            if not r.is_success:
                return False
            answer = r.json()["choices"][0]["message"]["content"].strip().upper()
            return answer.startswith("ALLOW")
    except Exception:
        return False

async def make_image(prompt, size):
    payload = {"model": IMAGE_MODEL, "prompt": prompt, "size": size, "n": 1}
    async with sem:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(API_BASE + "/images/generations", headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
            item = r.json()["data"][0]
    if item.get("url"):
        return item["url"]
    if item.get("b64_json"):
        raw = base64.b64decode(item["b64_json"])
        filename = f"{int(time.time()*1000)}_{hashlib.sha256(raw).hexdigest()[:12]}.png"
        sb.storage.from_(SUPABASE_BUCKET).upload(filename, raw, {"content-type": "image/png", "upsert": "false"})
        return sb.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
    raise RuntimeError("No image returned by TokenClub")

class GenReq(BaseModel):
    prompt: str
    size: str = "1024x1024"

@app.get("/")
async def root():
    f = ROOT / "webapp" / "index.html"
    if not f.exists():
        raise HTTPException(status_code=404, detail="Web App not found")
    return FileResponse(f)

@app.head("/")
async def root_head():
    return {}

@app.get("/health")
async def health():
    return {"ok": True, "service": "ImagesGPT"}

@app.get("/api/me")
async def me(x_telegram_init_data: str | None = Header(default=None)):
    user = current_sync(x_telegram_init_data)
    result = sb.table("history").select("id", count="exact").eq("user_id", user["user_id"]).eq("status", "done").execute()
    return {"user": {"user_id": user["user_id"], "username": user.get("username", ""), "full_name": user.get("full_name", ""), "balance": user.get("balance", 0), "created_at": user.get("created_at"), "id": user["user_id"], "total_images": result.count or 0}}

@app.get("/api/history")
async def history(x_telegram_init_data: str | None = Header(default=None)):
    user = current_sync(x_telegram_init_data)
    result = sb.table("history").select("id,prompt,size,status,image_url,created_at").eq("user_id", user["user_id"]).order("id", desc=True).limit(30).execute()
    return {"items": result.data or []}

@app.post("/api/generate")
async def generate(q: GenReq, x_telegram_init_data: str | None = Header(default=None)):
    user = current_sync(x_telegram_init_data)
    prompt = q.prompt.strip()
    size = q.size if q.size in {"1024x1024", "1536x1024", "1024x1536"} else "1024x1024"
    if not prompt:
        raise HTTPException(status_code=400, detail="Введите описание")
    if len(prompt) > 2000:
        raise HTTPException(status_code=400, detail="Промпт слишком длинный")
    if user["balance"] < IMAGE_COST:
        raise HTTPException(status_code=402, detail="Недостаточно монет")
    if not await moderate(prompt):
        raise HTTPException(status_code=400, detail="Запрос не прошёл модерацию")
    if not reserve(user["user_id"]):
        raise HTTPException(status_code=402, detail="Недостаточно монет")
    history_id = addhist(user["user_id"], prompt, size, "processing")
    try:
        image_url = await make_image(prompt, size)
        upd(history_id, "done", image_url)
        fresh = ensure(user["user_id"], user.get("username", ""), user.get("full_name", ""))
        return {"ok": True, "image_url": image_url, "balance": fresh["balance"]}
    except Exception as e:
        balance(user["user_id"], IMAGE_COST)
        upd(history_id, "error")
        raise HTTPException(status_code=502, detail="Генерация не удалась: " + str(e)[:250])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
