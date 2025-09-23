# models.py - Versão Otimizada com Índices
from datetime import datetime
from sqlalchemy import DateTime, Index, text
from sqlalchemy import Integer, String, func, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class ItemModel(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_code: Mapped[str] = mapped_column(String(120), index=True)  # Adicionado índice
    num_ped_ecf: Mapped[int] = mapped_column(Integer, nullable=True, index=True)  # Adicionado índice
    num_cupom: Mapped[int] = mapped_column(Integer, nullable=True, index=True)  # Adicionado índice
    num_caixa: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    vl_total: Mapped[float] = mapped_column(Float, index=True)  # Adicionado índice para ordenações por valor
    operation_type: Mapped[str] = mapped_column(String(120), index=True)  # Já tinha índice
    success: Mapped[bool] = mapped_column(Boolean, index=True)  # Adicionado índice para filtros por status
    message: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True  # Já tinha índice
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # === ÍNDICES COMPOSTOS OTIMIZADOS PARA QUERIES ESPECÍFICAS ===
    __table_args__ = (
        # Índice original mantido
        Index('ix_items_created_at_operation_type', 'created_at', 'operation_type'),
        
        # Índices compostos para queries do dashboard
        Index('ix_items_date_success_operation', 'created_at', 'success', 'operation_type'),
        Index('ix_items_caixa_date_operation', 'num_caixa', 'created_at', 'operation_type'),
        Index('ix_items_success_year_operation', 
              text('success, EXTRACT(year FROM created_at), operation_type')),
        Index('ix_items_success_year_month_operation', 
              text('success, EXTRACT(year FROM created_at), EXTRACT(month FROM created_at), operation_type')),
        
        # Índice para agregações por data
        Index('ix_items_date_only', text('DATE(created_at)')),
        
        # Índice para ordenação por created_at descendente (para queries de amostra)
        Index('ix_items_created_at_desc', text('created_at DESC')),
        
        # Índice para filtros por valor total
        Index('ix_items_value_date', 'vl_total', 'created_at'),
        
        # Índice para análises por ticket_code
        Index('ix_items_ticket_date', 'ticket_code', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"Item(id={self.id!r}, ticket_code={self.ticket_code!r}, num_ped_ecf={self.num_ped_ecf!r}, vl_total={self.vl_total!r}, operation_type={self.operation_type!r}, success={self.success!r}, message={self.message!r})"

# === SCRIPT SQL PARA CRIAÇÃO MANUAL DOS ÍNDICES (se necessário) ===
"""
-- Execute estes comandos SQL diretamente no banco se os índices não forem criados automaticamente:

-- Índices básicos (se ainda não existirem)
CREATE INDEX IF NOT EXISTS ix_items_ticket_code ON items(ticket_code);
CREATE INDEX IF NOT EXISTS ix_items_num_ped_ecf ON items(num_ped_ecf);
CREATE INDEX IF NOT EXISTS ix_items_num_cupom ON items(num_cupom);
CREATE INDEX IF NOT EXISTS ix_items_vl_total ON items(vl_total);
CREATE INDEX IF NOT EXISTS ix_items_success ON items(success);

-- Índices compostos otimizados
CREATE INDEX IF NOT EXISTS ix_items_date_success_operation ON items(created_at, success, operation_type);
CREATE INDEX IF NOT EXISTS ix_items_caixa_date_operation ON items(num_caixa, created_at, operation_type);
CREATE INDEX IF NOT EXISTS ix_items_success_year_operation ON items(success, EXTRACT(year FROM created_at), operation_type);
CREATE INDEX IF NOT EXISTS ix_items_success_year_month_operation ON items(success, EXTRACT(year FROM created_at), EXTRACT(month FROM created_at), operation_type);
CREATE INDEX IF NOT EXISTS ix_items_date_only ON items(DATE(created_at));
CREATE INDEX IF NOT EXISTS ix_items_created_at_desc ON items(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_items_value_date ON items(vl_total, created_at);
CREATE INDEX IF NOT EXISTS ix_items_ticket_date ON items(ticket_code, created_at);

-- Para PostgreSQL, também considere estes índices parciais para melhor performance:
CREATE INDEX IF NOT EXISTS ix_items_success_true ON items(created_at, operation_type) WHERE success = true;
CREATE INDEX IF NOT EXISTS ix_items_success_false ON items(created_at, operation_type) WHERE success = false;
CREATE INDEX IF NOT EXISTS ix_items_manual_validation ON items(created_at, success) WHERE operation_type = 'MANUAL_VALIDATION';
CREATE INDEX IF NOT EXISTS ix_items_automatic_validation ON items(created_at, success) WHERE operation_type = 'AUTOMATIC_VALIDATION';

-- Estatísticas para o otimizador de queries (execute periodicamente)
ANALYZE items;
"""