from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LugarTrabajo(Base):
    __tablename__ = "lugar_trabajo"

    id_lugar_trabajo: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )

    empresa_institucion: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    cargo: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    telefono_trabajo: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    email_laboral: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    id_direccion: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("direccion.id_direccion"),
        nullable=False,
    )
