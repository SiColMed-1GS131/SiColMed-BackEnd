from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MedicoEspecialidad(Base):
    __tablename__ = "medico_especialidad"

    id_medico_especialidad: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )
    id_especialidad: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("especialidad.id_especialidad"),
        nullable=False,
    )
