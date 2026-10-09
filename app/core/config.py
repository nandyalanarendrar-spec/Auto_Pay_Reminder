import os

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
except ImportError:
    pass

class Settings:
    PROJECT_NAME: str = "Autopay Guard"
    API_V1_STR: str = "/api/v1"
    SUPABASE_URL: str = os.getenv("VITE_SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("VITE_GEMINI_API_KEY", "")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/integrations/google-calendar/callback")

    # Setu Account Aggregator (sandbox) - credentials come from the Bridge dashboard
    SETU_CLIENT_ID: str = os.getenv("SETU_CLIENT_ID", "")
    SETU_CLIENT_SECRET: str = os.getenv("SETU_CLIENT_SECRET", "")
    SETU_PRODUCT_INSTANCE_ID: str = os.getenv("SETU_PRODUCT_INSTANCE_ID", "")
    SETU_BASE_URL: str = os.getenv("SETU_BASE_URL", "")
    SETU_AUTH_URL: str = os.getenv("SETU_AUTH_URL", "https://orgservice-prod.setu.co/v1/users/login")

    # WhatsApp Meta Cloud API Configuration
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WHATSAPP_BUSINESS_PHONE_NUMBER: str = os.getenv("WHATSAPP_BUSINESS_PHONE_NUMBER", "15551911379")

settings = Settings()
