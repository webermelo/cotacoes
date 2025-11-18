import streamlit as st
import requests
import re

def buscar_dados_cliente(cnpj: str):
    """
    Busca dados do cliente na API da ReceitaWS (mesma lógica do script desktop),
    mas levantando exceções em vez de usar messagebox.
    """
    # Remove tudo que não for número
    cnpj_limpo = re.sub(r"\D", "", cnpj)

    if len(cnpj_limpo) != 14:
        raise ValueError("CNPJ inválido. Digite 14 dígitos (com ou sem pontuação).")

    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}"

    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Falha ao conectar à API da ReceitaWS: {e}")

    if response.status_code != 200:
        try:
            dados_erro = response.json()
            msg = dados_erro.get("message", str(dados_erro))
        except Exception:
            msg = response.text
        raise RuntimeError(f"Erro na consulta à API (HTTP {response.status_code}): {msg}")

    try:
        dados = response.json()
    except ValueError:
        raise RuntimeError("Resposta inválida da API (não é JSON).")

    if dados.get("status") != "OK":
        message = dados.get("message", "Erro desconhecido na API da ReceitaWS.")
        raise RuntimeError(message)

    endereco = f'{dados.get("logradouro", "")}, {dados.get("numero", "")} - {dados.get("bairro", "")}'
    cidade_uf_cep = f'{dados.get("municipio", "")} - {dados.get("uf", "")}, CEP: {dados.get("cep", "")}'
    telefone = dados.get("telefone", "")

    return {
        "razao_social": dados.get("nome", ""),
        "endereco": endereco,
        "cidade_uf_cep": cidade_uf_cep,
        "telefone": telefone,
    }



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

    if st.button("Buscar dados do cliente"):
        if not cnpj.strip():
            st.error("Informe um CNPJ para buscar.")
        else:
            try:
                dados = buscar_dados_cliente(cnpj)
                st.success("Dados encontrados com sucesso!")
                st.write(f"**Razão Social:** {dados['razao_social']}")
                st.write(f"**Endereço:** {dados['endereco']}")
                st.write(f"**Cidade/UF/CEP:** {dados['cidade_uf_cep']}")
                if dados.get("telefone"):
                    st.write(f"**Telefone:** {dados['telefone']}")

                # Guardamos em dados_cliente para usar depois (PDF, Excel...)
                dados_cliente.update(dados)

            except Exception as e:
                st.error(f"Erro ao buscar dados do cliente: {e}")


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
