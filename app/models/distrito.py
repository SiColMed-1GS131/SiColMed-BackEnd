from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Distrito(Base):
    __tablename__ = "distrito"

    id_distrito: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )
    id_provincia: Mapped[int] = mapped_column(
        Integer, ForeignKey("provincia.id_provincia"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(
        Text, nullable=False
    )
