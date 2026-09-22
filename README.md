# ImagesGPT WebApp

GitHub stores the code; Render runs the Python bot/API.

1. Upload this folder to GitHub.
2. Create a Render Web Service from that repository.
3. Build: `pip install -r requirements.txt`
4. Start: `python main.py`
5. Add Render environment variables: BOT_TOKEN, ADMIN_ID, API_KEY, WEBAPP_URL.
6. Deploy once, copy the Render URL, put it into WEBAPP_URL, then redeploy.

Do NOT put BOT_TOKEN or API_KEY into GitHub.
SQLite is used for the first version. Render's default filesystem is ephemeral, so for production use a persistent disk or PostgreSQL.


## Supabase setup

1. Create a Supabase project.
2. Open SQL Editor.
3. Paste and run `supabase/schema.sql`.
4. Copy Project URL into `SUPABASE_URL`.
5. Copy the **service_role** key into `SUPABASE_KEY`.
6. Keep that key only on Render. Never put it in `webapp/` or GitHub.
7. Deploy the Render service.

Supabase now stores:
- users and balances in PostgreSQL
- generation history in PostgreSQL
- generated base64 images in Supabase Storage

Telegram `initData` is still the login/authentication mechanism. The browser never receives the Supabase service-role key.
