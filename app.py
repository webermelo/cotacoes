import streamlit as st
from io import BytesIO

from core import (
    buscar_dados_cliente,
    obter_numero_sequencial,
    adicionar_dados_excel,
    gerar_cotacao_pdf,
    BASE_DIR,
)

st.set_page_config(page_title="Cotações Mokka/Moica", page_icon="📄")

# ---------------------------
# Estado inicial (sessão)
# ---------------------------
if "dados_cliente" not in st.session_state:
    st.session_state["dados_cliente"] = {}
if "cnpj_cliente" not in st.session_state:
    st.session_state["cnpj_cliente"] = ""


def format_currency(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


st.title("Gerador de Cotações – Mokka / Moica")
st.write("Versão web da ferramenta de cotações. Preencha os dados e gere o PDF.")

# ---------------------------
# 1) Seleção da empresa
# ---------------------------
st.subheader("1. Empresa")
empresa = st.selectbox("Selecione a empresa:", ["Mokka", "Moica"])

# ---------------------------
# 2) Responsável
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
# 3) Condições comerciais
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
# 4) Dados do Cliente
# ---------------------------
st.subheader("4. Dados do Cliente")

modo_cliente = st.radio(
    "Forma de preenchimento dos dados do cliente:",
    ["Buscar pelo CNPJ (API)", "Preencher manualmente"],
)

# Trabalhamos em cima do estado salvo
dados_cliente_state = st.session_state["dados_cliente"]

if modo_cliente == "Buscar pelo CNPJ (API)":
    cnpj_cliente = st.text_input(
        "CNPJ do Cliente",
        placeholder="00.000.000/0000-00",
        value=st.session_state["cnpj_cliente"],
    )
    # Atualiza na sessão
    st.session_state["cnpj_cliente"] = cnpj_cliente

    if st.button("Buscar dados do cliente"):
        if not cnpj_cliente.strip():
            st.error("Informe um CNPJ para buscar.")
        else:
            try:
                dados = buscar_dados_cliente(cnpj_cliente)
                st.success("Dados encontrados com sucesso!")
                st.write(f"**Razão Social:** {dados['razao_social']}")
                st.write(f"**Endereço:** {dados['endereco']}")
                st.write(f"**Cidade/UF/CEP:** {dados['cidade_uf_cep']}")
                if dados.get("telefone"):
                    st.write(f"**Telefone:** {dados['telefone']}")

                # Salva os dados do cliente na sessão
                st.session_state["dados_cliente"] = dados

            except Exception as e:
                st.error(f"Erro ao buscar dados do cliente: {e}")

    # Mostrar dados atuais do cliente (se já estiverem na sessão)
    if st.session_state["dados_cliente"]:
        dc = st.session_state["dados_cliente"]
        st.info(
            f"Cliente atual: **{dc.get('razao_social', '')}** - "
            f"{dc.get('endereco', '')} - {dc.get('cidade_uf_cep', '')}"
        )

else:
    # modo manual: usamos os valores já salvos como default
    razao = st.text_input(
        "Razão Social",
        value=dados_cliente_state.get("razao_social", ""),
    )
    endereco = st.text_input(
        "Endereço",
        value=dados_cliente_state.get("endereco", ""),
    )
    cidade_uf_cep = st.text_input(
        "Cidade - UF - CEP",
        value=dados_cliente_state.get("cidade_uf_cep", ""),
    )
    telefone = st.text_input(
        "Telefone",
        value=dados_cliente_state.get("telefone", ""),
    )

    st.session_state["dados_cliente"] = {
        "razao_social": razao,
        "endereco": endereco,
        "cidade_uf_cep": cidade_uf_cep,
        "telefone": telefone,
    }

# Para o resto do app, usamos sempre estes:
dados_cliente = st.session_state["dados_cliente"]
cnpj_cliente = st.session_state["cnpj_cliente"]

# ---------------------------
# 5) Itens da Cotação
# ---------------------------
st.subheader("5. Itens da Cotação")

qtd_itens = st.number_input(
    "Quantos itens deseja adicionar?",
    min_value=1,
    max_value=20,
    value=1,
    step=1,
)

itens = []
total_geral = 0.0

for i in range(int(qtd_itens)):
    st.markdown(f"### Item {i + 1}")

    col1, col2 = st.columns(2)
    with col1:
        produto = st.text_input("Produto", key=f"produto_{i}")
    with col2:
        ncm = st.text_input("NCM", key=f"ncm_{i}")

    descricao = st.text_area("Descrição", key=f"descricao_{i}")

    col3, col4, col5 = st.columns(3)
    with col3:
        preco_unitario = st.number_input(
            "Preço unitário (R$)",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key=f"preco_{i}",
        )
    with col4:
        quantidade = st.number_input(
            "Quantidade",
            min_value=1,
            value=1,
            step=1,
            key=f"quant_{i}",
        )
    with col5:
        prazo_entrega = st.text_input("Prazo de entrega", key=f"prazo_{i}")

    total_item = preco_unitario * quantidade
    total_geral += total_item

    st.write(
        f"**Total do item {i + 1}: R$ {total_item:,.2f}"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

    itens.append(
        {
            "produto": produto,
            "descricao": descricao,
            "preco_unitario": format_currency(preco_unitario),
            "quantidade": str(int(quantidade)),
            "ncm": ncm,
            "total": format_currency(total_item),
            "prazo_entrega": prazo_entrega,
        }
    )

st.markdown(
    f"## TOTAL DA COTAÇÃO: R$ {total_geral:,.2f}"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)

# ---------------------------
# 6) Gerar PDF e salvar Excel
# ---------------------------
st.subheader("6. Gerar Cotação")

if st.button("Gerar PDF"):
    # Validações básicas
    if not dados_cliente.get("razao_social"):
        st.error("Preencha os dados do cliente ou faça a busca pelo CNPJ antes de gerar a cotação.")
    elif not prazo_pagamento.strip():
        st.error("Informe o prazo de pagamento.")
    elif not itens:
        st.error("Adicione pelo menos um item.")
    else:
        # Valida itens
        for idx, item in enumerate(itens, start=1):
            if not all(
                [
                    item["produto"].strip(),
                    item["descricao"].strip(),
                    item["preco_unitario"],
                    item["quantidade"],
                    item["ncm"].strip(),
                    item["total"],
                    item["prazo_entrega"].strip(),
                ]
            ):
                st.error(f"Preencha todos os campos do item {idx}.")
                st.stop()

        try:
            numero_sequencial = obter_numero_sequencial()

            # Gera PDF em memória
            buffer = BytesIO()
            gerar_cotacao_pdf(
                dados_cliente=dados_cliente,
                itens=itens,
                prazo_pagamento=prazo_pagamento,
                frete_tipo=frete_tipo,
                output=buffer,
                numero_sequencial=numero_sequencial,
                responsavel=responsavel,
                empresa=empresa,
            )

            buffer.seek(0)

            # Salva PDF localmente no servidor (pasta do app)
            nome_arquivo = f"Cotacao_{empresa}_{numero_sequencial}.pdf"
            caminho_pdf = BASE_DIR / nome_arquivo
            with open(caminho_pdf, "wb") as f:
                f.write(buffer.getvalue())

            # Registra no Excel
            adicionar_dados_excel(
                dados_cliente=dados_cliente,
                itens=itens,
                numero_sequencial=numero_sequencial,
                cliente_tipo=cliente_tipo,
                cnpj_cliente=cnpj_cliente if modo_cliente == "Buscar pelo CNPJ (API)" else "",
            )

            st.success(f"Cotação #{numero_sequencial} gerada com sucesso!")

            st.download_button(
                label="Baixar PDF da cotação",
                data=buffer,
                file_name=nome_arquivo,
                mime="application/pdf",
            )

            st.info(f"Arquivo também salvo no servidor em: {caminho_pdf}")

        except Exception as e:
            st.error(f"Erro ao gerar a cotação: {e}")
