from datetime import date

from sqlalchemy import Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Movimiento(Base):
    __tablename__ = "movimiento"

    id_movimiento: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    fecha: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    descripcion: Mapped[str] = mapped_column(
        Text, nullable=False
    )
