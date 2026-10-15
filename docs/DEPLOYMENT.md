# Deployment guide

Three hosted pieces: **Vercel** (frontend and the Setu relay), **Render** (FastAPI backend) and **Supabase**
(database and auth).

## Frontend and relay: Vercel

- Deploys automatically on every push to `main`.
- `vercel.json` pins functions to the Mumbai region (`bom1`) and gives the relay 30 seconds.
- Variables (Production): `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL` (the Render URL) and
  `SETU_RELAY_KEY`.
- Preview deployments are protected by Vercel Authentication, so open them while signed in to Vercel.

## Backend: Render

- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`, Python 3.11.
- Auto-deploy can be switched on under Settings > Build & Deploy > Auto-Deploy > On Commit. When it is off, use
  Manual Deploy > Deploy latest commit after each merge.
- Variables: `VITE_SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `VITE_SUPABASE_ANON_KEY`, `DATABASE_URL`, `GEMINI_API_KEY`,
  Google OAuth (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`), WhatsApp
  (`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_BUSINESS_ACCOUNT_ID`), Setu (`SETU_CLIENT_ID`,
  `SETU_CLIENT_SECRET`, `SETU_PRODUCT_INSTANCE_ID`, `SETU_BASE_URL`) and the relay (`SETU_RELAY_URL`,
  `SETU_RELAY_KEY`).
- The free tier sleeps after 15 minutes of inactivity. Pinging `/health` every five minutes (for example with
  cron-job.org) keeps it awake.

## Setu relay

Setu's login endpoint refuses some hosting providers' addresses with an AWS load balancer `403`. The relay
(`api/setu-relay.js`) forwards the backend's Setu requests from Mumbai:

- `SETU_RELAY_URL` = `https://<your-site>.vercel.app/api/setu-relay`
- `SETU_RELAY_KEY` = the same long random string on Vercel and on Render
- the function accepts only `POST`, requires the key, and only talks to the Setu hosts it allow-lists.

Leave `SETU_RELAY_URL` empty to call Setu directly.

Other Setu notes: one data fetch per consent per day; an approval link works once; set the Redirect URL to the frontend
and the notification URL to `/api/v1/bank/webhook` in the Bridge dashboard.

## Database: Supabase

- Run the files in `db/`, starting with `supabase_schema.sql`. The backend also applies idempotent `ALTER` statements
  at startup, so the schema converges on its own.
- Row-level security must stay enabled on every public table (the Security Advisor flags any that are not).

## Secrets

Never commit `.env`. Keep the Supabase secret key, the Setu client secret and the relay key only in the host
dashboards, and rotate them if they are ever shown in a screenshot or chat.
