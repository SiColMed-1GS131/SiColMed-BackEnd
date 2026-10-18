from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LogInicioSesion(Base):
    __tablename__ = "log_inicio_sesion"

    id_log: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    id_usuario: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=False,
    )

    resultado: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
