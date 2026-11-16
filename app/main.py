# Tablero de Importaciones y Dependencias
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import DBAPIError

# Tablero de Importanciones y dependencias menores
from app.config import settings
from app.database import get_db
from app.errors import manejar_error_bd
from app.routers import cuentas
from app.routers.medicos_directorio import router as router_medicos_directorio
from app.routers import solicitudes_cambio, catalogos
from app.routers import medicos
from app.routers import auth
from app.routers import movimientos, reportes


app = FastAPI(title="API Certificaciones Médicas - Panamá")
app.add_exception_handler(DBAPIError, manejar_error_bd)
app.include_router(router_medicos_directorio)
app.include_router(solicitudes_cambio.router)
app.include_router(catalogos.router)
app.include_router(medicos.router)
app.include_router(cuentas.router)
app.include_router(auth.router)
app.include_router(movimientos.router)
app.include_router(reportes.router)

def origenes_cors(valor: str) -> list[str]:
    """Separa CORS_ORIGINS por comas y quita espacios y la barra final de cada origen.

    El navegador envía el Origin sin barra final (http://localhost:3000); si el
    .env trae "http://localhost:3000/", la comparación falla y el preflight da 400.
    """
    return [o.strip().rstrip("/") for o in valor.split(",")]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_cors(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


# Métodos principales
@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "ok",
            "version" : "4"}