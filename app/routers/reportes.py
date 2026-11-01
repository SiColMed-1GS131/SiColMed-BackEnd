from fastapi import APIRouter, Depends
from app.schemas.reportes import BalanceGeneralResponse
from app.schemas.movimientos import RangoFechasParams
from app.services import reportes as reportes_service

router = APIRouter(prefix="/reportes", tags=["Reportes Contables"])

@router.get("/balance-general", response_model=BalanceGeneralResponse)
def calcular_balance_general(rango: RangoFechasParams = Depends()):
    filas = reportes_service.calcular_balance_general(rango)
    return {"filas": filas}