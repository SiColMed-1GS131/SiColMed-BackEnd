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
from app.routers import solicitudes_cambio
from app.routers.medicos_directorio import router as router_medicos_directorio

app = FastAPI(title="API Certificaciones Médicas - Panamá")
app.add_exception_handler(DBAPIError, manejar_error_bd)
app.include_router(router_medicos_directorio)
app.include_router(solicitudes_cambio.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
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