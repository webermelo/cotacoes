import streamlit as st
from io import BytesIO

from core import (
    buscar_dados_cliente,
    obter_numero_sequencial,
    adicionar_dados_excel,
    gerar_cotacao_pdf,
    BASE_DIR,
)

# ---------------------------
# CONFIGURAÇÃO INICIAL
# ---------------------------
st.set_page_config(page_title="Cotações Mokka/Moica", page_icon="📄")

# Estado inicial
if "dados_cliente" not in st.session_state:
    st.session_state["dados_cliente"] = {}
if "cnpj_cliente" not in st.session_state:
    st.session_state["cnpj_cliente"] = ""


def format_currency(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


st.title("Gerador de Cotações – Mokka / Moica")
st.write("Versão web da ferramenta de cotações. Preencha os dados e gere o PDF.")


# ---------------------------
# 1) EMPRESA
# ---------------------------
st.subheader("1. Empresa")
empresa = st.selectbox("Selecione a empresa:", ["Mokka", "Moica"])


# ---------------------------
# 2) RESPONSÁVEL
# ---------------------------
st.subheader("2. Responsável pela Cotação")
responsavel_nome = st.selectbox(
    "Selecione o responsável:",
    ["Weber Melo", "Thiago Velicev", "Giulia Armelin", "Letícia Casale"],
)

responsaveis = {
    "Weber Melo": {
        "nome": "Weber Melo",
        "telefone": "(11) 98477-9490",
        "email": "atendimento@mokka-sensors.com.br",
        "site1": "www.mokka-sensors.com.br",
        "site2": "www.camerastermicas.com.br",
    },
    "Thiago Velicev": {
        "nome": "Thiago Velicev",
        "telefone": "(11) 91000-9205",
        "email": "atendimento@mokka-sensors.com.br",
        "site1": "www.mokka-sensors.com.br",
        "site2": "www.camerastermicas.com.br",
    },
    "Giulia Armelin": {
        "nome": "Giulia Armelin",
        "telefone": "(11) 91000-9205",
        "email": "atendimento@mokka-sensors.com.br",
        "site1": "www.mokka-sensors.com.br",
        "site2": "www.camerastermicas.com.br",
    },
    "Letícia Casale": {
        "nome": "Letícia Casale",
        "telefone": "(11) 91000-9205",
        "email": "atendimento@mokka-sensors.com.br",
        "site1": "www.mokka-sensors.com.br",
        "site2": "www.camerastermicas.com.br",
    },
}

responsavel = responsaveis[responsavel_nome]


# ---------------------------
# 3) CONDIÇÕES COMERCIAIS
# ---------------------------
st.subheader("3. Condições comerciais")

col_tipo, col_prazo, col_frete = st.columns(3)

with col_tipo:
    cliente_tipo = st.selectbox("Tipo de Cliente", ["Cliente Final", "Revenda"])

with col_prazo:
    prazo_pagamento = st.text_input("Prazo de Pagamento", value="30 dias")

with col_frete:
    frete_tipo = st.selectbox("Frete", ["FOB", "CIF"])


# ---------------------------
# 4) DADOS DO CLIENTE
# ---------------------------
st.subheader("4. Dados do Cliente")

modo_cliente = st.radio(
    "Forma de preenchimento dos dados do cliente:",
    ["Buscar pelo CNPJ (API)", "Preencher manualmente"],
)

dados_cliente_state = st.session_state["dados_cliente"]

if modo_cliente == "Buscar pelo CNPJ (API)":
    cnpj_cliente = st.text_input(
        "CNPJ do Cliente",
        placeholder="00.000.000/0000-00",
        value=st.session_state["cnpj_cliente"],
    )

    st.session
