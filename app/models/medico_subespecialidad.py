from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MedicoSubespecialidad(Base):
    __tablename__ = "medico_subespecialidad"

    id_medico_subespecialidad: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )
    id_subespecialidad: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("subespecialidad.id_subespecialidad"),
        nullable=False,
    )
