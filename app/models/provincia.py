from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Provincia(Base):
    __tablename__ = "provincia"

    id_provincia: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    # Código oficial de la DPA 2025 (ANATI/INEC). FIX DE EMERGENCIA de Desarrollo,
    # pendiente de revisión por Base de Datos (migración 5d1f0c7a9e42).
    codigo: Mapped[str | None] = mapped_column(
        Text, unique=True, nullable=True
    )
