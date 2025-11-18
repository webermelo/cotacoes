import streamlit as st

st.set_page_config(page_title="Cotações Mokka/Moica", page_icon="📄")

st.title("Gerador de Cotações – Mokka / Moica")

st.write("Versão inicial da interface web. Vamos montar passo a passo a cotação completa.")

# ---------------------------
# 1) Seleção da empresa
# ---------------------------
st.subheader("1. Empresa")
empresa = st.selectbox("Selecione a empresa:", ["Mokka", "Moica"])

# ---------------------------
# 2) Responsável
# ---------------------------
st.subheader("2. Responsável pela Cotação")
responsavel = st.selectbox(
    "Selecione o responsável:",
    ["Weber Melo", "Thiago Velicev", "Giulia Armelin", "Letícia Casale"],
)

# ---------------------------
# 3) Dados do Cliente
# ---------------------------
st.subheader("3. Dados do Cliente")

modo_cliente = st.radio(
    "Forma de preenchimento dos dados do cliente:",
    ["Buscar pelo CNPJ (API)", "Preencher manualmente"],
)

dados_cliente = {}

if modo_cliente == "Buscar pelo CNPJ (API)":
    cnpj = st.text_input("CNPJ do Cliente", placeholder="00.000.000/0000-00")
    st.info("A busca via API será implementada no próximo passo.")
    if st.button("Buscar dados do cliente"):
        st.warning("Função de busca ainda será integrada.")

else:
    dados_cliente["razao_social"] = st.text_input("Razão Social")
    dados_cliente["endereco"] = st.text_input("Endereço")
    dados_cliente["cidade_uf_cep"] = st.text_input("Cidade - UF - CEP")
    dados_cliente["telefone"] = st.text_input("Telefone")

# ---------------------------
# 4) Itens da cotação (estrutura inicial)
# ---------------------------
st.subheader("4. Itens da Cotação")

qtd_itens = st.number_input("Quantos itens deseja adicionar?", min_value=1, max_value=20, value=1)

st.info("A parte dos itens será construída no próximo passo.")

# ---------------------------
# 5) Gerar PDF (placeholder)
# ---------------------------
st.subheader("5. Gerar Cotação")

if st.button("Gerar PDF"):
    st.error("A geração de PDF ainda será implementada.")
