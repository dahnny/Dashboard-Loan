from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: str

    # Supabase Auth
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_audience: str = "authenticated"

    # Supabase Storage
    supabase_storage_bucket: str = "loan-documents"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Mono Direct Debit
    mono_base_url: str | None = None
    mono_secret_key: str | None = None
    mono_public_key: str | None = None
    class Config:
        env_file=".env"
    
settings = Settings()

