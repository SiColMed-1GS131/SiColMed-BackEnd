from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Asociacion(Base):
    __tablename__ = "asociacion"

    id_asociacion: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )
