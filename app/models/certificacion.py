from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Certificacion(Base):
    __tablename__ = "certificacion"

    id_certificacion: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )

    vigente: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )

    fecha_obtencion: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    puntaje: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    fecha_expiracion: Mapped[date] = mapped_column(
        Date, nullable=False
    )
