# crud.py

from datetime import datetime
from sqlalchemy import func, or_, String
from sqlalchemy.orm import Session, Query
import pandas as pd
from app import models

# ... (COLUMN_MAP and _apply_filters_and_sorting remain the same) ...
# Mapeia os nomes das colunas que o usuário vê para os atributos do modelo SQLAlchemy.
# Isso é mais seguro e flexível do que passar strings diretamente na query.
COLUMN_MAP = {
    "Ticket Code": models.ItemModel.ticket_code,
    "Num Cupom": models.ItemModel.num_cupom,
    "Num Caixa": models.ItemModel.num_caixa,
    "Hostname": models.ItemModel.hostname,
    "Num Ped ECF": models.ItemModel.num_ped_ecf,
    "Valor Total": models.ItemModel.vl_total,
    "Criado em": models.ItemModel.created_at,
}


def _apply_filters_and_sorting(
    query: Query,
    start_date: datetime, 
    end_date: datetime, 
    operation_types: tuple[str, ...],
    search_term: str | None = None,
    sort_by: str | None = None,
    sort_order: str = 'desc',
    apply_sorting: bool = True # Add this new parameter
):
    """Função auxiliar para aplicar filtros, busca e ordenação."""
    # Filtros de data e tipo de operação (sempre aplicados)
    query = query.filter(
        models.ItemModel.created_at.between(start_date, end_date),
        models.ItemModel.operation_type.in_(operation_types)
    )

    # Filtro de busca (se um termo for fornecido)
    if search_term:
        # Busca em várias colunas. Converte colunas numéricas para String para usar 'ilike'.
        search_filter = or_(
            models.ItemModel.ticket_code.ilike(f"%{search_term}%"),
            models.ItemModel.num_cupom.cast(String).ilike(f"%{search_term}%"),
            models.ItemModel.num_caixa.cast(String).ilike(f"%{search_term}%")
        )
        query = query.filter(search_filter)

    # Apply sorting only if requested
    if apply_sorting:
      if sort_by and sort_by in COLUMN_MAP:
          column_to_sort = COLUMN_MAP[sort_by]
          if sort_order == 'asc':
              query = query.order_by(column_to_sort.asc())
          else:
              query = query.order_by(column_to_sort.desc())
      else:
          # Uma ordenação padrão é importante para a consistência da paginação
          query = query.order_by(models.ItemModel.created_at.desc())
        
    return query


def get_items_by_date(
    db: Session, 
    start_date: datetime, 
    end_date: datetime, 
    operation_types: tuple[str, ...],
):
    """Busca itens de forma paginada, com busca e ordenação."""
    base_query = db.query(
        models.ItemModel.ticket_code,
        models.ItemModel.num_cupom,
        models.ItemModel.num_caixa,
        models.ItemModel.hostname,
        models.ItemModel.num_ped_ecf,
        models.ItemModel.vl_total,
        models.ItemModel.operation_type,
        models.ItemModel.success,
        models.ItemModel.created_at
    )
    
    query = _apply_filters_and_sorting(
        base_query, start_date, end_date, operation_types,
    )
    
    return query.all()


def count_items_by_date(
    db: Session, 
    start_date: datetime, 
    end_date: datetime, 
    operation_types: tuple[str, ...],
    search_term: str | None = None
) -> int:
    """Conta o total de itens para os filtros, incluindo o de busca."""
    base_query = db.query(func.count(models.ItemModel.id))
    
    # Apply filters but NOT sorting for the count query
    query = _apply_filters_and_sorting(
        base_query, start_date, end_date, operation_types, search_term, apply_sorting=False
    )
    
    # O scalar() retorna um único valor, que é o resultado do COUNT
    result = query.scalar()
    return result if result is not None else 0
    
# ... (rest of the file remains the same) ...
def get_kpi_data(db: Session, start_date: datetime, end_date: datetime, operation_types: tuple[str, ...]):
    """Calcula os KPIs diretamente no banco de dados."""
    current_year = datetime.now().year
    current_month = datetime.now().month

    base_query = db.query(models.ItemModel).filter(
        models.ItemModel.created_at.between(start_date, end_date),
        models.ItemModel.operation_type.in_(operation_types),
        models.ItemModel.success == True
    )
    
    # Usamos .with_entities para especificar o que contar, o que pode ser mais eficiente
    desconto_ano_total = base_query.filter(
        func.extract('year', models.ItemModel.created_at) == current_year
    ).with_entities(func.count()).scalar() or 0

    desconto_mes_atual = base_query.filter(
        func.extract('year', models.ItemModel.created_at) == current_year,
        func.extract('month', models.ItemModel.created_at) == current_month
    ).with_entities(func.count()).scalar() or 0

    validacao_manual = base_query.filter(
        func.extract('year', models.ItemModel.created_at) == current_year,
        models.ItemModel.operation_type == 'MANUAL_VALIDATION'
    ).with_entities(func.count()).scalar() or 0
    
    validacao_automatica = base_query.filter(
        func.extract('year', models.ItemModel.created_at) == current_year,
        models.ItemModel.operation_type == 'AUTOMATIC_VALIDATION'
    ).with_entities(func.count()).scalar() or 0

    return {
        "desconto_ano": desconto_ano_total,
        "desconto_mes_atual": desconto_mes_atual,
        "validacao_manual": validacao_manual,
        "validacao_automatica": validacao_automatica
    }


def get_daily_counts(db: Session, start_date: datetime, end_date: datetime, operation_types: tuple[str, ...]):
    """Retorna a contagem de sucessos e falhas agrupadas por dia."""
    result = (
        db.query(
            func.date(models.ItemModel.created_at).label('data'),
            models.ItemModel.success,
            func.count(models.ItemModel.id).label('quantidade')
        )
        .filter(
            models.ItemModel.created_at.between(start_date, end_date),
            models.ItemModel.operation_type.in_(operation_types)
        )
        .group_by('data', models.ItemModel.success)
        .order_by('data')
        .all()
    )
    return [
        {"Data": row.data, "Status": "Sucesso" if row.success else "Falha", "Quantidade": row.quantidade}
        for row in result
    ]
    
    
def get_hostname_caixa_distribution(db: Session, start_date: datetime, end_date: datetime, operation_types: tuple[str, ...]):
    """Retorna a contagem e a soma do valor total por junção de hostname e num_caixa."""
    result = (
        db.query(
            models.ItemModel.hostname,
            models.ItemModel.num_caixa,
            func.count(models.ItemModel.id).label('contagem'),
            func.sum(models.ItemModel.vl_total).label('valor_total')
        )
        .filter(
            models.ItemModel.created_at.between(start_date, end_date),
            models.ItemModel.operation_type.in_(operation_types)
        )
        .group_by(models.ItemModel.hostname, models.ItemModel.num_caixa)
        .order_by(models.ItemModel.hostname, models.ItemModel.num_caixa)
        .all()
    )
    return pd.DataFrame(result, columns=['Hostname', 'Num Caixa', 'Contagem', 'Valor Total'])
