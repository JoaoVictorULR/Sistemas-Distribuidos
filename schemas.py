from pydantic import BaseModel

class ClimaRequest(BaseModel):
    cidade: str

class ClimaResponse(BaseModel):
    cidade: str
    temperatura: float
    condicao: str
