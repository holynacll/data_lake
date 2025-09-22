import locale
from math import ceil
from datetime import datetime, timedelta
import altair as alt

import streamlit as st
import pandas as pd

from app.database import SessionLocal
from app.crud import get_items_by_date
from app.config import settings

# --- Configurações Iniciais e Constantes ---
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

# Constantes para evitar "magic strings"
MANUAL_VALIDATION = "MANUAL_VALIDATION"
AUTOMATIC_VALIDATION = "AUTOMATIC_VALIDATION"


# Coloque esta função junto com as outras funções auxiliares
@st.cache_data(ttl=1200)  # Cache de 20 minutos (1200 segundos)
def fetch_data_from_db(start_date, end_date, operation_types):
    """
    Função cacheada para buscar dados do banco de dados.
    A consulta real ao DB só será executada se o cache expirar ou se os parâmetros mudarem.
    """
    types_tuple = tuple(sorted(operation_types)) # Converte a lista para tupla para que seja "hashable" pelo cache
    with SessionLocal() as db:
        items = get_items_by_date(db, start_date, end_date, types_tuple) # type: ignore
        # É importante retornar dados serializáveis (não objetos SQLAlchemy complexos)
        # Sua conversão para data_list já resolve isso.
        return [
            {
                "Ticket Code": item.ticket_code,
                "Status": "Sucesso" if item.success else "Falha",
                "Num Cupom": item.num_cupom,
                "Num Ped ECF": item.num_ped_ecf,
                "Valor Total": item.vl_total,
                "Validação Manual": "Sim" if item.operation_type == MANUAL_VALIDATION else "Não",
                "Criado em": item.created_at.strftime("%Y/%m/%d"),
                # "operation_type": item.operation_type, # Adicionei para a conversão ser completa
                # "success": item.success
            }
            for item in items
        ]


# --- Funções Auxiliares com Type Hinting ---
@st.cache_data(show_spinner="Carregando dados...")
def load_data(data: list[dict]) -> pd.DataFrame:
    """Converte uma lista de dicionários em um DataFrame do Pandas."""
    return pd.DataFrame(data)

def authenticate_api_key(api_key: str) -> bool:
    """Valida a chave de API."""
    if not settings.API_KEY:
        raise ValueError("A chave de API não está configurada no ambiente.")
    return api_key == settings.API_KEY

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Análise de Descontos")
st.title("Análise de Descontos")

# Autenticação (descomente se precisar)
# api_key = st.text_input("Enter API Key:", type="password")
# if not authenticate_api_key(api_key):
#     st.error("Chave de API inválida. Acesso negado.")
#     st.stop()

# --- Barra Lateral de Parâmetros ---
with st.sidebar:
    st.header("⚙️ Configuração de Parâmetros")
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

# --- Lógica Principal e Exibição de Dados ---
operation_types_to_fetch = []
if validacao_manual_check:
    operation_types_to_fetch.append(MANUAL_VALIDATION)
if validacao_automatica_check:
    operation_types_to_fetch.append(AUTOMATIC_VALIDATION)

if not operation_types_to_fetch:
    st.warning("Selecione pelo menos um tipo de validação.")
    st.stop()

# Use o context manager para a sessão do DB
# with SessionLocal() as db:
#     items = get_items_by_date(db, start_date, end_date, operation_types_to_fetch)

data_list = fetch_data_from_db(start_date, end_date, operation_types_to_fetch)

if not data_list:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
else:
    df = load_data(data_list)
    df['Data'] = pd.to_datetime(df["Criado em"], format="%Y/%m/%d")

    # --- INÍCIO DA SEÇÃO DE KPIs ---
    st.subheader("Resumo Geral")
    
    # Prepara os dados para os KPIs
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Filtra o DataFrame para os cálculos
    sucesso_df = df[df['Status'] == 'Sucesso']
    sucesso_df_ano = sucesso_df[sucesso_df['Data'].dt.year == current_year]
    
    # KPI 1: Sucesso no ano
    desconto_ano = sucesso_df_ano.shape[0]
    
    # KPI 2: Sucesso no mês
    desconto_mes_atual = sucesso_df[(sucesso_df['Data'].dt.year == current_year) & (sucesso_df['Data'].dt.month == current_month)].shape[0]

    # KPI 3: Validação Manual
    validacao_manual = sucesso_df_ano[sucesso_df_ano['Validação Manual'] == 'Sim'].shape[0]

    # KPI 4: Validação Automática
    validacao_automatica = sucesso_df_ano[sucesso_df_ano['Validação Manual'] == 'Não'].shape[0]

    # Exibe os KPIs em 4 colunas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label=f"Descontos em {current_year}", value=desconto_ano)
    with col2:
        st.metric(label=f"Descontos Manuais em {current_year}", value=validacao_manual)
    with col3:
        st.metric(label=f"Descontos Automáticos em {current_year}", value=validacao_automatica)
    with col4:
        st.metric(label="Descontos no Mês Atual", value=desconto_mes_atual)

    
    st.divider() # Adiciona uma linha divisória para separar os KPIs do resto do dashboard
    # --- FIM DA SEÇÃO DE KPIs ---


    # --- Gráfico de Barras (com Altair) ---
    count_df = (
        df.groupby(by=["Data", "Status"])
        .size()
        .reset_index(name="Quantidade")
    )

    color_scale = alt.Scale(
        domain=['Sucesso', 'Falha'],
        range=['#2ca02c', '#d62728'] # Verde e Vermelho
    )

    chart = alt.Chart(count_df).mark_bar().encode(
        x=alt.X('Data:T', title='Descontado em', axis=alt.Axis(format="%b %d")),
        y=alt.Y('Quantidade:Q', title='Quantidade de Descontos'),
        color=alt.Color('Status:N', scale=color_scale, title='Status'),
        tooltip=[
            alt.Tooltip('Data:T', format='%d/%m/%Y'), 
            'Status', 
            'Quantidade'
        ]
    ).properties(
        title='Contagem de Descontos por Dia'
    )
    st.altair_chart(chart, use_container_width=True)


    # --- Gráficos de Pizza ---
    st.subheader("Distribuição dos Descontos")
    col1_pie, col2_pie = st.columns(2)

    with col1_pie:
        validation_counts = df['Validação Manual'].value_counts().reset_index()
        validation_counts.columns = ['Tipo de Validação', 'Contagem']
        validation_counts['Tipo de Validação'] = validation_counts['Tipo de Validação'].map(
            {'Sim': 'Manual', 'Não': 'Automática'}
        )


        pie_chart_validation = alt.Chart(validation_counts).mark_arc(outerRadius=120).encode(
            theta=alt.Theta("Contagem:Q", stack=True),
            color=alt.Color("Tipo de Validação:N", title="Tipo de Validação"),
            tooltip=["Tipo de Validação", "Contagem"]
        ).properties(
            title="Descontos por Tipo de Validação"
        )
        st.altair_chart(pie_chart_validation, use_container_width=True)

    with col2_pie:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Contagem']

        pie_chart_status = alt.Chart(status_counts).mark_arc(outerRadius=120).encode(
            theta=alt.Theta("Contagem:Q", stack=True),
            color=alt.Color("Status:N", scale=color_scale, title="Status"),
            tooltip=["Status", "Contagem"]
        ).properties(
            title="Descontos por Status (Sucesso/Falha)"
        )
        st.altair_chart(pie_chart_status, use_container_width=True)

    
    # --- Tabela Analítica ---
    st.subheader("Tabela Analítica")

    st.dataframe(
        data=df.drop(columns=['Data']), # Remove a coluna 'Data' que foi criada apenas para os gráficos
        hide_index=True,
        column_config={
            "Valor Total": st.column_config.NumberColumn(
                label="Valor Total",
                help="Valor total do desconto em Reais (R$).",
                format="R$ %.2f"
            ),
            "Criado em": st.column_config.DateColumn(
                label="Criado em",
                help="Data em que o desconto foi criado.",
                format="DD/MM/YYYY"
            )
        }
    )

    # --- Exportação para CSV ---
    # csv = df.to_csv(index=False).encode("utf-8")
    # st.download_button(
    #     label="📥 Exportar para CSV",
    #     data=csv,
    #     file_name=f"descontos_{start_date_input}_a_{end_date_input}.csv",
    #     mime="text/csv",
    # )