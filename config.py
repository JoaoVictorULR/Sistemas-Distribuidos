# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Open-Meteo não exige chave, mas deixamos aqui para demonstrar padrão
    OPEN_METEO_BASE: str = "https://api.open-meteo.com/v1/forecast"
    # timeout para chamadas externas (segundos)
    HTTP_TIMEOUT: float = 5.0
    CACHE_TTL_SECONDS: int = 60  # cache simples por 60s

    class Config:
        env_file = ".env"  # opcional: carregar .env se existir

settings = Settings()
