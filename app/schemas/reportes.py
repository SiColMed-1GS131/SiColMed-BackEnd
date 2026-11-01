from pydantic import BaseModel
from typing import List

class FilaBalanceGeneral(BaseModel):
    id_cuenta: int
    nombre_cuenta: str
    total_debito: float
    total_credito: float
    saldo: float

class BalanceGeneralResponse(BaseModel):
    filas: List[FilaBalanceGeneral]