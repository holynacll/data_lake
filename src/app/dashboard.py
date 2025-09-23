# app.py

import locale
from datetime import datetime
import altair as alt
import streamlit as st
import pandas as pd
from app.database import SessionLocal
from app.repository import (
    get_paginated_items_by_date, 
    count_items_by_date,
    get_kpi_data,
    get_daily_counts,
    get_caixa_distribution
)

# --- Configurações Iniciais e Constantes ---
st.set_page_config(layout="wide", page_title="Análise de Descontos")
try:
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "") # Fallback para o locale padrão

MANUAL_VALIDATION = "MANUAL_VALIDATION"
AUTOMATIC_VALIDATION = "AUTOMATIC_VALIDATION"
PAGE_SIZE = 100

# --- Funções de Busca de Dados Cacheadas ---

@st.cache_data(ttl=1200, show_spinner="Calculando KPIs...")
def fetch_kpi_data(start_date, end_date, operation_types):
    types_tuple = tuple(sorted(operation_types))
    with SessionLocal() as db:
        return get_kpi_data(db, start_date, end_date, types_tuple)

@st.cache_data(ttl=1200, show_spinner="Gerando gráfico de contagem...")
def fetch_daily_counts_data(start_date, end_date, operation_types):
    types_tuple = tuple(sorted(operation_types))
    with SessionLocal() as db:
        data = get_daily_counts(db, start_date, end_date, types_tuple)
        return pd.DataFrame(data)

@st.cache_data(ttl=1200, show_spinner="Gerando gráfico de distribuição...")
def fetch_caixa_distribution_data(start_date, end_date, operation_types):
    types_tuple = tuple(sorted(operation_types))
    with SessionLocal() as db:
        return get_caixa_distribution(db, start_date, end_date, types_tuple)

@st.cache_data(ttl=1200, show_spinner="Buscando dados da tabela...")
def fetch_paginated_table_data(start_date, end_date, operation_types, page, page_size, search_term, sort_by, sort_order):
    types_tuple = tuple(sorted(operation_types))
    skip = (page - 1) * page_size
    with SessionLocal() as db:
        items = get_paginated_items_by_date(
            db, start_date, end_date, types_tuple, skip, page_size,
            search_term, sort_by, sort_order
        )
        total_items = count_items_by_date(
            db, start_date, end_date, types_tuple, search_term
        )
        
        df = pd.DataFrame(items, columns=[
            "Ticket Code", "Num Cupom", "Num Caixa", "Num Ped ECF", "Valor Total",
            "Validação Manual", "Status", "Criado em"
        ])
        df['Validação Manual'] = df['Validação Manual'].apply(lambda x: "Sim" if x == MANUAL_VALIDATION else "Não")
        df['Status'] = df['Status'].apply(lambda x: "Sucesso" if x else "Falha")
        
        return df, total_items

# --- Início da Aplicação ---
st.title("📊 Análise de Descontos")

# --- Barra Lateral de Parâmetros ---
with st.sidebar:
    st.header("⚙️ Filtros")
    today = datetime.today()
    start_date_input = st.date_input("Data de Início", datetime(today.year, 1, 1))
    end_date_input = st.date_input("Data de Fim", today)

    start_date = datetime.combine(start_date_input, datetime.min.time())
    end_date = datetime.combine(end_date_input, datetime.max.time())

    if start_date > end_date:
        st.error("A data de início não pode ser maior que a data de fim.")
        st.stop()

    validacao_manual_check = st.checkbox("Validação Manual", value=True)
    validacao_automatica_check = st.checkbox("Validação Automática", value=True)

# --- Lógica Principal ---
operation_types_to_fetch = []
if validacao_manual_check:
    operation_types_to_fetch.append(MANUAL_VALIDATION)
if validacao_automatica_check:
    operation_types_to_fetch.append(AUTOMATIC_VALIDATION)

if not operation_types_to_fetch:
    st.warning("Selecione pelo menos um tipo de validação.")
    st.stop()

# --- Seção de KPIs ---
st.subheader("Resumo Geral")
kpi_data = fetch_kpi_data(start_date, end_date, operation_types_to_fetch)

if kpi_data['desconto_ano'] == 0 and kpi_data['desconto_mes_atual'] == 0:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

current_year = datetime.now().year
current_month_name = datetime.now().strftime('%B').capitalize()

col1, col2, col3, col4 = st.columns(4)
col1.metric(label=f"Descontos em {current_year}", value=f"{kpi_data['desconto_ano']:,}".replace(",", "."))
col2.metric(label=f"Manuais em {current_year}", value=f"{kpi_data['validacao_manual']:,}".replace(",", "."))
col3.metric(label=f"Automáticos em {current_year}", value=f"{kpi_data['validacao_automatica']:,}".replace(",", "."))
col4.metric(label=f"Descontos em {current_month_name}", value=f"{kpi_data['desconto_mes_atual']:,}".replace(",", "."))

st.divider()

# --- Seção de Gráficos ---
col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    count_df = fetch_daily_counts_data(start_date, end_date, operation_types_to_fetch)
    if not count_df.empty:
        color_scale = alt.Scale(domain=['Sucesso', 'Falha'], range=['#2ca02c', '#d62728'])
        chart = alt.Chart(count_df).mark_bar().encode(
            x=alt.X('Data:T', title='Data', axis=alt.Axis(format="%d %b")),
            y=alt.Y('Quantidade:Q', title='Quantidade'),
            color=alt.Color('Status:N', scale=color_scale, title='Status'),
            tooltip=[alt.Tooltip('Data:T', format='%d/%m/%Y'), 'Status', 'Quantidade']
        ).properties(title='Contagem de Descontos por Dia')
        st.altair_chart(chart, use_container_width=True)

with col_chart2:
    df_combinado = fetch_caixa_distribution_data(start_date, end_date, operation_types_to_fetch)
    if not df_combinado.empty:
        base = alt.Chart(df_combinado).encode(x=alt.X('Num Caixa:N', title='Número do Caixa', sort=None))
        barras = base.mark_bar().encode(
            y=alt.Y('Contagem:Q', title='Quantidade'),
            tooltip=[alt.Tooltip('Num Caixa'), alt.Tooltip('Contagem')]
        )
        linha = base.mark_line(color='red', point=True).encode(
            y=alt.Y('Valor Total:Q', title='Valor Acumulado (R$)'),
            tooltip=[alt.Tooltip('Num Caixa'), alt.Tooltip('Valor Total', format='R$,.2f')]
        )
        grafico_final = alt.layer(barras, linha).resolve_scale(y='independent').properties(
            title="Quantidade vs. Valor por Caixa"
        )
        st.altair_chart(grafico_final, use_container_width=True)

st.divider()

# --- Tabela Analítica ---
st.subheader("Tabela Analítica de Registros")

# Inicializa o estado da sessão
if 'page' not in st.session_state: st.session_state.page = 1
if 'search' not in st.session_state: st.session_state.search = ""
if 'sort_by' not in st.session_state: st.session_state.sort_by = "Criado em"
if 'sort_order' not in st.session_state: st.session_state.sort_order = "Decrescente"

# Controles de Busca e Ordenação
col_search, col_sort_by, col_sort_order = st.columns([2, 1, 1])

def on_change_search_sort():
    st.session_state.page = 1
    st.session_state.search = st.session_state.search_widget
    st.session_state.sort_by = st.session_state.sort_by_widget
    st.session_state.sort_order = st.session_state.sort_order_widget

col_search.text_input(
    "Buscar por Ticket, Cupom ou Caixa",
    key="search_widget",
    on_change=on_change_search_sort
)
col_sort_by.selectbox(
    "Ordenar por",
    options=["Criado em", "Valor Total", "Num Caixa", "Ticket Code"],
    key="sort_by_widget",
    on_change=on_change_search_sort
)
col_sort_order.selectbox(
    "Ordem",
    options=["Decrescente", "Crescente"],
    key="sort_order_widget",
    on_change=on_change_search_sort
)

sort_order_param = 'asc' if st.session_state.sort_order == "Crescente" else 'desc'

df_table, total_items = fetch_paginated_table_data(
    start_date, end_date, operation_types_to_fetch, 
    st.session_state.page, PAGE_SIZE, 
    st.session_state.search, 
    st.session_state.sort_by, 
    sort_order_param
)

total_pages = (total_items // PAGE_SIZE) + (1 if total_items % PAGE_SIZE > 0 else 0)
if total_pages == 0: total_pages = 1

st.write(f"Mostrando **{len(df_table)}** de **{total_items}** registros.")

st.dataframe(
    data=df_table,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Valor Total": st.column_config.NumberColumn(format="R$ %.2f"),
        "Criado em": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm")
    }
)

# Controles de paginação
col_nav1, col_nav2, _ = st.columns([1, 1, 4])
if col_nav1.button("⬅️ Anterior", disabled=(st.session_state.page <= 1)):
    st.session_state.page -= 1
    st.rerun()

if col_nav2.button("Próxima ➡️", disabled=(st.session_state.page >= total_pages)):
    st.session_state.page += 1
    st.rerun()

st.caption(f"Página {st.session_state.page} de {total_pages}")
