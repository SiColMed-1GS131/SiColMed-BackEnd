from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MedicoAsociacion(Base):
    __tablename__ = "medico_asociacion"

    id_medico_asociacion: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )
    id_asociacion: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("asociacion.id_asociacion"),
        nullable=False,
    )
