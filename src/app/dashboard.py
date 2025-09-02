import locale
from math import ceil
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from app.database import SessionLocal
from app.crud import get_items_by_date
from app.config import settings

locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
db = SessionLocal()

@st.cache_data(show_spinner=False)
def load_data(data):
    dataset = pd.DataFrame(data)
    return dataset

@st.cache_data(show_spinner=False)
def split_frame(input_df, rows):
    df = [input_df.loc[i : i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

if settings.API_KEY is None:
    raise ValueError("API key is not set. Please set the API key in your environment variables.")

def authenticate_api_key(api_key):
    if api_key != settings.API_KEY:
        return False
    return True

st.set_page_config(layout="wide")

st.title("Dashboard de Descontos")

# api_key = st.text_input("Enter API Key:", type="password")
# if not authenticate_api_key(api_key):
#     st.error("Invalid API key. Access denied.")
#     st.stop()


# Date range selection
with st.sidebar:
    st.title("Configuração")
    today = datetime.today()
    start_date_input = st.date_input("Data de Início", today - timedelta(days=7))
    end_date_input = st.date_input("Data de Fim", today)

    start_date = datetime.combine(start_date_input, datetime.min.time())
    end_date = datetime.combine(end_date_input, datetime.max.time())

    if start_date > end_date:
        st.error("A data de início não pode ser maior que a data de fim.")
    
    validacao_manual_check = st.checkbox("Validação Manual", value=True)
    validacao_automatica_check = st.checkbox("Validação Automática", value=True)
    # desconto_realizado_com_sucesso_check = st.checkbox("Desconto Realizado com Sucesso", value=True)
    # desconto_realizado_com_error_check = st.checkbox("Desconto Realizado com Erro", value=True)
    # desconto_realizado_com_sucesso_radio = st.radio("Desconto Realizado com Sucesso", options=["Sim", "Não"])
    

if start_date <= end_date:
    items = get_items_by_date(db, start_date, end_date)
    # items = [item for item in items if item.success == (desconto_realizado_com_sucesso_radio == "Sim")]
    # items_com_desconto_com_sucesso = [item for item in items if item.success and desconto_realizado_com_sucesso_check] if desconto_realizado_com_sucesso_check else []
    # items_com_desconto_com_error = [item for item in items if not item.success and desconto_realizado_com_error_check] if desconto_realizado_com_error_check else []
    # items = items_com_desconto_com_sucesso + items_com_desconto_com_error

    items_manual = [item for item in items if item.operation_type == "MANUAL_VALIDATION"] if validacao_manual_check else []
    items_automatic = [item for item in items if item.operation_type == "AUTOMATIC_VALIDATION"] if validacao_automatica_check else []
    items = items_manual + items_automatic



    if not items:
        st.warning("Nenhum item encontrado para o período selecionado.")
    else:
        # Convert to DataFrame
        data = [
            {
                "Ticket Code": item.ticket_code,
                "Num Cupom": item.num_cupom,
                "Num Ped ECF": item.num_ped_ecf,
                "Valor Total": item.vl_total,
                "Validação Manual": "Sim" if item.operation_type == "MANUAL_VALIDATION" else "Não",
                "Desconto Realizado": "Sim" if item.success else "Não",
                "Criado em": item.created_at.strftime("%d/%m/%Y"),
            }
            for item in items
        ]
        df = load_data(data)

        # Pagination
        pagination = st.container()

        bottom_menu = st.columns((4, 1, 1))
        with bottom_menu[2]:
            batch_size = st.selectbox("Page Size", options=[10, 25, 50, 100])
        with bottom_menu[1]:
            total_pages = (
                ceil(len(df) / batch_size) if int(len(df) / batch_size) > 0 else 1
            )
            current_page = st.number_input(
                "Page", min_value=1, max_value=total_pages, step=1
            )
        with bottom_menu[0]:
            st.markdown(f"Page **{current_page}** of **{total_pages}** ")

        pages = split_frame(df, batch_size)
        pagination.dataframe(data=pages[current_page - 1])

        # Display data
        # st.dataframe(df)

        # Export to CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Exportar para CSV",
            data=csv,
            file_name=f"items_{start_date}_to_{end_date}.csv",
            mime="text/csv",
        )

        st.header("Análise de Operações")
        df["Data"] = pd.to_datetime(df["Criado em"], format="%d/%m/%Y")
        count_df = (
            df.groupby(by=["Data", "Desconto Realizado"])
            .size()
            .reset_index(name="Quantidade")
        )

        fig = st.line_chart(
            count_df,
            x="Data",  # exibe a string formatada
            y="Quantidade",
            x_label="Descontado em",
            y_label="Quantidade de Descontos",
            color="Desconto Realizado",
        )

db.close()
