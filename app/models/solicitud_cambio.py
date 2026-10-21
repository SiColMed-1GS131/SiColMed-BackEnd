from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SolicitudCambio(Base):
    __tablename__ = "solicitud_cambio"

    id_solicitud_cambio: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_usuario: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=True,
    )

    id_medico: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("medico.id_medico"),
        nullable=False,
    )

    estado: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'PENDIENTE'"),
    )

    fecha_solicitud: Mapped[datetime] = mapped_column(
        DateTime, nullable=False
    )

    fecha_respuesta: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    comentario: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    cambios: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
