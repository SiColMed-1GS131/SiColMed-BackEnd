from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Medico(Base):
    __tablename__ = "medico"

    id_medico: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_usuario: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("usuario.id_usuario"),
        nullable=True,
    )

    numero_idoneidad: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )

    numero_registro_medico: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )

    cedula: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    primer_nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    segundo_nombre: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    apellido_paterno: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    apellido_materno: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    foto: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    fecha_nacimiento: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    telefono_residencial: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    celular: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    email_personal: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    id_direccion: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("direccion.id_direccion"),
        nullable=False,
    )
