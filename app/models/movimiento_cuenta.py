from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MovimientoCuenta(Base):
    __tablename__ = "movimiento_cuenta"

    __table_args__ = (
        CheckConstraint(
            "monto > 0",
            name="ck_movimiento_cuenta_monto_positivo",
        ),
    )

    id_movimiento_cuenta: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )

    id_movimiento: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movimiento.id_movimiento"),
        nullable=False,
    )

    id_cuenta: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cuenta.id_cuenta"),
        nullable=False,
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )

    tipo: Mapped[str] = mapped_column(
        Text, nullable=False
    )
