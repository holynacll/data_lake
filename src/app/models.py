from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer, String, func, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ItemModel(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_code: Mapped[str] = mapped_column(String(120))
    num_ped_ecf: Mapped[int] = mapped_column(Integer, nullable=True)
    num_cupom: Mapped[int] = mapped_column(Integer, nullable=True)
    vl_total: Mapped[float] = mapped_column(Float)
    operation_type: Mapped[str] = mapped_column(String(120))
    success: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, ticket_code={self.ticket_code!r}, num_ped_ecf={self.num_ped_ecf!r}, vl_total={self.vl_total!r}, operation_type={self.operation_type!r}, success={self.success!r}, message={self.message!r})"
    