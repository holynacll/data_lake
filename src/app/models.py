# models.py
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Index, Text, text
from sqlalchemy import Integer, String, func, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ItemModel(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_code: Mapped[str] = mapped_column(String(120), index=True)
    num_ped_ecf: Mapped[str] = mapped_column(String(60), nullable=True, index=True)
    num_cupom: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)  # era Integer
    num_caixa: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    hostname: Mapped[str] = mapped_column(String(120), nullable=True, index=True)
    vl_total: Mapped[float] = mapped_column(Float, index=True)
    operation_type: Mapped[str] = mapped_column(String(120), index=True)
    success: Mapped[bool] = mapped_column(Boolean, index=True)
    message: Mapped[str] = mapped_column(Text)  # era String(200)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index('ix_items_created_at_operation_type', 'created_at', 'operation_type'),
        Index('ix_items_date_success_operation', 'created_at', 'success', 'operation_type'),
        Index('ix_items_caixa_date_operation', 'num_caixa', 'created_at', 'operation_type'),
        Index('ix_items_hostname_date_operation', 'hostname', 'created_at', 'operation_type'),
        Index('ix_items_success_year_operation',
              text('success, EXTRACT(year FROM created_at), operation_type')),
        Index('ix_items_success_year_month_operation',
              text('success, EXTRACT(year FROM created_at), EXTRACT(month FROM created_at), operation_type')),
        Index('ix_items_date_only', text('DATE(created_at)')),
        Index('ix_items_created_at_desc', text('created_at DESC')),
        Index('ix_items_value_date', 'vl_total', 'created_at'),
        Index('ix_items_ticket_date', 'ticket_code', 'created_at'),
    )

    def __repr__(self) -> str:
        return (
            f"Item(id={self.id!r}, ticket_code={self.ticket_code!r}, "
            f"num_ped_ecf={self.num_ped_ecf!r}, vl_total={self.vl_total!r}, "
            f"operation_type={self.operation_type!r}, success={self.success!r}, "
            f"message={self.message!r})"
        )