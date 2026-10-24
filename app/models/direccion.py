from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Direccion(Base):
    __tablename__ = "direccion"

    id_direccion: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    apartado_postal: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    calle: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    edificio: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    numero_direccion: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    id_provincia: Mapped[int] = mapped_column(
        Integer, ForeignKey("provincia.id_provincia"), nullable=False
    )
    id_distrito: Mapped[int] = mapped_column(
        Integer, ForeignKey("distrito.id_distrito"), nullable=False
    )
    id_corregimiento: Mapped[int] = mapped_column(
        Integer, ForeignKey("corregimiento.id_corregimiento"), nullable=False
    )
