from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Corregimiento(Base):
    __tablename__ = "corregimiento"

    id_corregimiento: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_distrito: Mapped[int] = mapped_column(
        Integer, ForeignKey("distrito.id_distrito"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    # Código oficial de la DPA 2025 (ANATI/INEC). FIX DE EMERGENCIA de Desarrollo,
    # pendiente de revisión por Base de Datos (migración 5d1f0c7a9e42).
    codigo: Mapped[str | None] = mapped_column(
        Text, unique=True, nullable=True
    )
