from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    nombre: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
