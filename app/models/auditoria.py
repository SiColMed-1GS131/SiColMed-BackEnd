from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id_auditoria: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    id_usuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=False,
    )

    id_rol: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rol.id_rol"),
        nullable=False,
    )

    accion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    entidad: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    id_registro: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
