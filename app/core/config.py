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
    database_url: str | None = None

    # Supabase Auth
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_audience: str = "authenticated"

    # Supabase Storage
    supabase_storage_bucket: str = "loan-bucket"

    # Redis
    redis_host: str
    redis_port: int
    redis_db: int
    redis_username: str | None = None
    redis_password: str | None = None
    redis_url: str | None = None
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    

    # Mono Direct Debit
    mono_base_url: str | None = None
    mono_secret_key: str | None = None
    mono_public_key: str | None = None
    class Config:
        env_file=".env"
        
    @property
    def broker_url(self) -> str:
        """Return the Celery broker URL, falling back to Redis settings.

        Order of precedence:
        1. Explicit `celery_broker_url`
        2. Constructed Redis URL from host/port/db
        """
        if self.celery_broker_url:
            return self.celery_broker_url
        return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    @property
    def result_backend(self) -> str:
        """Return the Celery result backend URL with Redis fallback."""
        if self.celery_result_backend:
            return self.celery_result_backend
        return f"redis://{self.redis_username}:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"

    
settings = Settings()

