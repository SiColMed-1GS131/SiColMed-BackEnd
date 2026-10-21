from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EstudioMedico(Base):
    __tablename__ = "estudio_medico"

    id_estudio: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )

    tipo_estudio: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    titulo: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    institucion: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    lugar: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    fecha: Mapped[date] = mapped_column(
        Date, nullable=False
    )
