from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Subespecialidad(Base):
    __tablename__ = "subespecialidad"

    id_subespecialidad: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_especialidad: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("especialidad.id_especialidad"),
        nullable=False,
    )
    nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )
