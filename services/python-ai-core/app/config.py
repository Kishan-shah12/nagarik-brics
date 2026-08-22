"""Application configuration loaded from environment variables.

Uses pydantic-settings BaseSettings to securely load the GEMINI_API_KEY
and all other configuration from the environment. No secrets are ever
hardcoded in source files.

Environment Variables:
    GEMINI_API_KEY: Required. Google Gemini API key for NLP processing.
    GEMINI_MODEL: Model identifier. Default: gemini-2.5-flash.
    PORT: Server port. Default: 8080.
    LOG_LEVEL: Logging level. Default: INFO.
    CORS_ORIGINS: Comma-separated allowed origins. Default: * (MVP only).
    RATE_LIMIT_PER_MINUTE: Max requests per minute per IP. Default: 60.
    JAVA_INGESTION_URL: Java service URL. Default: http://localhost:8081.

Example:
    Export variables before running::

        export GEMINI_API_KEY="your-api-key-here"
        uvicorn app.main:app --port 8080
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All configuration is externalized to environment variables. The
    GEMINI_API_KEY is the only required variable — the rest have sensible
    defaults for development and Docker deployment.

    Attributes:
        gemini_api_key: Google Gemini API key. Required, never hardcoded.
        gemini_model: Gemini model identifier for NLP processing.
        port: HTTP server port.
        log_level: Python logging level string.
        cors_origins: Comma-separated list of allowed CORS origins.
        rate_limit_per_minute: Maximum requests per minute per client IP.
        java_ingestion_url: Base URL of the Java Ingestion service.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Required ----
    gemini_api_key: str = Field(
        ...,
        min_length=10,
        description="Google Gemini API key. Must be set via environment.",
    )

    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier for high-speed reasoning.",
    )

    # ---- Supabase Configuration ----
    supabase_url: str = Field(
        default="",
        description="Supabase project URL.",
    )
    
    supabase_key: str = Field(
        default="",
        description="Supabase anonymous/publishable key.",
    )

    # ---- Server ----
    port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="HTTP server port.",
    )

    log_level: str = Field(
        default="INFO",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Python logging level.",
    )

    # ---- CORS ----
    cors_origins: str = Field(
        default="*",
        description="Comma-separated allowed CORS origins. Use * for MVP only.",
    )

    # ---- Rate Limiting ----
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Maximum requests per minute per client IP.",
    )

    # ---- Inter-Service Communication ----
    java_ingestion_url: str = Field(
        default="http://localhost:8081",
        description="Base URL of the Java Ingestion microservice.",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list.

        Returns:
            List of allowed origin strings.
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Factory function to create and cache application settings.

    Returns:
        Validated Settings instance loaded from environment.

    Raises:
        pydantic.ValidationError: If GEMINI_API_KEY is missing or
            any field fails validation constraints.
    """
    return Settings()
