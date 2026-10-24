from sqlalchemy import Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Cuenta(Base):
    __tablename__ = "cuenta"

    id_cuenta: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    nombre: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )

    tipo: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    activa: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
