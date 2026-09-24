from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import health, auth, subscriptions, emis, mock_generator, analytics, dashboard, integrations, notifications, chatbot, admin, ai, reports, whatsapp

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autopay Guard Backend API - Subscription, EMI, Bank Transactions & Autopay Tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_sanity_check():
    """
    Module DB-10: Startup Safety Check.
    Verifies database connection and core table existence on server launch.
    """
    print("==================================================")
    print("🛡️ AUTOPAY GUARD - STARTUP DB SANITY CHECK")
    print("==================================================")
    try:
        from sqlalchemy import text
        from app.core.database import engine
        if engine is not None:
            with engine.connect() as conn:
                res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")).fetchall()
                tables = [r[0] for r in res]
                expected = ["subscriptions", "emis", "transactions"]
                missing = [t for t in expected if t not in tables]
                
                if missing:
                    print(f"⚠️ WARNING: Missing database tables in Supabase public schema: {missing}")
                    print("Run 'supabase_schema.sql' in Supabase SQL Editor to restore missing tables.")
                else:
                    conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS calendar_sync_error VARCHAR(1024);"))
                    conn.execute(text("ALTER TABLE emis ADD COLUMN IF NOT EXISTS calendar_sync_error VARCHAR(1024);"))
                    conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_start_date DATE;"))
                    conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_end_date DATE;"))
                    conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS expected_first_payment_date DATE;"))
                    conn.execute(text("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_free_trial BOOLEAN DEFAULT FALSE;"))
                    conn.commit()
                    print("✅ PASS: Connected to Supabase PostgreSQL (All core tables verified).")
        else:
            print("⚠️ WARNING: DATABASE_URL not initialized. Check .env configuration.")
    except Exception as err:
        print("⚠️ Note on Direct PostgreSQL Connection (DNS/IPv6):", err)
        try:
            from app.core.security import get_supabase_client
            client = get_supabase_client()
            res = client.from_("subscriptions").select("id").limit(1).execute()
            print("✅ PASS: Connected to Supabase REST API (HTTPS). Database tables verified & accessible!")
        except Exception as rest_err:
            print("❌ Supabase REST Check Error:", rest_err)
    print("==================================================")

    # Launch in-process background scheduler for billing rollover
    try:
        from app.services.background_scheduler_service import start_scheduler
        start_scheduler()
    except Exception as sched_err:
        print("⚠️ Could not start background scheduler:", sched_err)

@app.on_event("shutdown")
def shutdown_scheduler():
    try:
        from app.services.background_scheduler_service import stop_scheduler
        stop_scheduler()
    except Exception as err:
        pass

# Include API Routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(emis.router, prefix="/api/v1")
app.include_router(mock_generator.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(chatbot.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} Backend API",
        "health_check": "/health",
        "docs": "/docs"
    }
