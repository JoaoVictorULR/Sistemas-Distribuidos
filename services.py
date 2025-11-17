# services.py
import httpx
from cachetools import TTLCache, cached
from typing import Tuple
from config import settings

# cache simples em memória: até 100 chaves, TTL definido em settings
cache = TTLCache(maxsize=100, ttl=settings.CACHE_TTL_SECONDS)

# mapeamento simples de cidades de exemplo -> coordenadas (lat, lon)
CIDADES_MT = {
    "cuiaba": (-15.601, -56.097),
    "varzea-grande": (-15.646, -56.132),
    "sinop": (-11.860, -55.510),
    "rondonopolis": (-16.470, -54.635),
    "caceres": (-16.070, -57.681),
}

def _get_coords(cidade: str) -> Tuple[float, float]:
    key = cidade.lower().strip()
    if key not in CIDADES_MT:
        raise ValueError("Cidade não suportada. Cadastre ou use coordenadas.")
    return CIDADES_MT[key]

@cached(cache)  # decorador para cachear respostas por TTL
def fetch_clima_sync(lat: float, lon: float) -> dict:
    """
    Chamada síncrona para Open-Meteo (httpx). Podemos usar versão async se desejar.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        # opcional: timezone, hourly etc
    }
    try:
        with httpx.Client(timeout=settings.HTTP_TIMEOUT) as client:
            r = client.get(settings.OPEN_METEO_BASE, params=params)
            r.raise_for_status()
            return r.json()
    except httpx.RequestError as e:
        # erros de rede, DNS, timeout
        raise RuntimeError(f"Erro de requisição ao provedor de clima: {e}") from e
    except httpx.HTTPStatusError as e:
        # 4xx/5xx
        raise RuntimeError(f"Resposta inválida do provedor: {e.response.status_code}") from e

def analisar_motor(cidade: str) -> dict:
    """
    Função de alto nível: pega coords, busca clima, aplica regras e devolve um dict.
    """
    lat, lon = _get_coords(cidade)
    payload = fetch_clima_sync(lat, lon)

    # estrutura do Open-Meteo quando current_weather=True:
    # payload["current_weather"] -> {"temperature": 20.3, "windspeed": 5.1, ...}
    current = payload.get("current_weather", {})
    temp = current.get("temperature")
    # Open-Meteo não dá umidade diretamente no current_weather; isso é só exemplo.
    # Para umidade você pode usar parâmetros hourly ou outra API.
    # Aqui vamos simular umidade (se não existir) para a lógica.
    umidade = payload.get("relativehumidity_2m") or 40  # fallback

    # chuva: como exemplo, não disponível no current_weather básico
    chuva = 0.0

    # regras simples
    if umidade is not None and umidade < 30 and (chuva == 0 or chuva is None):
        risco = "ALTO"
        recomendacao = "Risco elevado de incêndio. Evitar queimadas e aumentar vigilância."
    elif temp is not None and temp > 33:
        risco = "MODERADO"
        recomendacao = "Alto calor. Atentar para irrigação e segurança."
    else:
        risco = "BAIXO"
        recomendacao = "Condições normais."

    return {
        "cidade": cidade,
        "temperatura": temp,
        "umidade": umidade,
        "chuva": chuva,
        "risco_incendio": risco,
        "recomendacao": recomendacao
    }
