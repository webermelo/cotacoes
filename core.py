from pathlib import Path
from datetime import datetime
import re
import requests
import openpyxl

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from PIL import Image

# Diretório base do projeto (onde estão os logos, Excel, etc.)
BASE_DIR = Path(__file__).parent

EXCEL_FILE = BASE_DIR / "dados_cotacoes.xlsx"
COTACAO_SEQUENCE_FILE = BASE_DIR / "cotacao_sequence.txt"


# -----------------------------
# Número sequencial da cotação
# -----------------------------
def obter_numero_sequencial(filepath: Path = COTACAO_SEQUENCE_FILE) -> int:
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            numero_atual = int(file.read().strip())
    except FileNotFoundError:
        numero_atual = 3456  # Número inicial se o arquivo não existir

    novo_numero = numero_atual + 1

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(str(novo_numero))

    return numero_atual


# -----------------------------
# Buscar dados do cliente (API)
# -----------------------------
def buscar_dados_cliente(cnpj: str):
    """
    Busca dados do cliente na API da ReceitaWS.
    Lança exceções em caso de erro.
    """
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


# -----------------------------
# Registrar dados no Excel
# -----------------------------
def adicionar_dados_excel(
    dados_cliente: dict,
    itens: list[dict],
    numero_sequencial: int,
    cliente_tipo: str,
    cnpj_cliente: str = "",
):
    """
    Adiciona os dados da cotação em dados_cotacoes.xlsx.
    """
    if not EXCEL_FILE.exists():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(
            [
                "Data da Cotação",
                "Número da Cotação",
                "Razão Social do Cliente",
                "CNPJ do Cliente",
                "Produto",
                "Total (item)",
                "Cliente Final ou Revenda",
            ]
        )
    else:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        ws = wb.active

    data_cotacao = datetime.now().strftime("%d/%m/%Y")

    for item in itens:
        ws.append(
            [
                data_cotacao,
                numero_sequencial,
                dados_cliente.get("razao_social", ""),
                cnpj_cliente,
                item.get("produto", ""),
                item.get("total", "").replace(".", ","),
                cliente_tipo,
            ]
        )

    wb.save(EXCEL_FILE)


# -----------------------------
# Utilitário de quebra de linha
# -----------------------------
def wrap_text(text, char_limit=85):
    words = text.split()
    lines = []
    line = []
    for word in words:
        if len(" ".join(line + [word])) > char_limit:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    return lines


# -----------------------------
# Gerar PDF da cotação
# -----------------------------
def gerar_cotacao_pdf(
    dados_cliente: dict,
    itens: list[dict],
    prazo_pagamento: str,
    frete_tipo: str,
    output,  # pode ser caminho (str/Path) ou BytesIO
    numero_sequencial: int,
    responsavel: dict,
    empresa: str,
):
    """
    Gera o PDF da cotação. 'output' pode ser um Path/str ou um buffer em memória (BytesIO).
    O layout é baseado no script desktop.
    """

    if empresa == "Mokka":
        logo_filename = "Logo-Mokka-Sensors.jpg"
        footer_text = "Mokka Com. de Bens de Consumo Ltda - CNPJ: 21.220.932/0001-10"
        logo_percent = 0.35
        logo_y_position_adjustment = 2 * cm
    else:
        logo_filename = "Logo-Moica.jpg"
        footer_text = "Moica Com. de Bens de Consumo Ltda - CNPJ: 42.044.083/0001-60"
        logo_percent = 0.11
        logo_y_position_adjustment = 0.35 * cm

    logo_path = BASE_DIR / logo_filename
    if not logo_path.exists():
        raise FileNotFoundError(f"Arquivo de logo não encontrado: {logo_path}")

    logo_image = Image.open(logo_path)
    original_width, original_height = logo_image.size

    width, height = A4
    desired_width = width * logo_percent
    aspect_ratio = original_height / original_width
    desired_height = desired_width * aspect_ratio

    c = canvas.Canvas(str(output), pagesize=A4)

    page_number = 1

    def draw_header(cnv, page_num):
        logo_y_position = height - logo_y_position_adjustment - desired_height
        cnv.drawImage(str(logo_path), 2 * cm, logo_y_position,
                      width=desired_width, height=desired_height)

        line_y_position = logo_y_position - 0.3 * cm
        cnv.setLineWidth(0.5)
        cnv.line(1 * cm, line_y_position, width - 1 * cm, line_y_position)

        data_criacao = datetime.now().strftime("%d/%m/%Y")
        cnv.setFont("Helvetica", 12)
        cnv.drawString(width - 5 * cm, height - 3 * cm, f"Data: {data_criacao}")

        cnv.setFont("Helvetica", 10)
        cnv.drawString(2 * cm, height - 4 * cm, f"Responsável: {responsavel['nome']}")
        cnv.drawString(2 * cm, height - 4.5 * cm, f"Contato: {responsavel['telefone']}")
        cnv.drawString(2 * cm, height - 5 * cm, f"{responsavel['email']}")
        cnv.drawString(2 * cm, height - 5.5 * cm, f"{responsavel['site1']}")
        cnv.drawString(2 * cm, height - 6 * cm, f"{responsavel['site2']}")

        footer_y_position = 1.5 * cm
        cnv.setLineWidth(0.5)
        cnv.line(1 * cm, footer_y_position + 0.5 * cm,
                 width - 1 * cm, footer_y_position + 0.5 * cm)
        cnv.setFont("Helvetica", 10)
        cnv.drawCentredString(width / 2, footer_y_position, footer_text)
        cnv.drawString(width - 5 * cm, footer_y_position, f"Página {page_num}")

    # Cabeçalho da primeira página
    draw_header(c, page_number)

    # Título com número sequencial
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 7 * cm, f"Cotação #{numero_sequencial}")

    # Subtítulo Cliente
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, height - 8.5 * cm, "Cliente")

    # Dados do cliente
    c.setFont("Helvetica", 12)
    client_y = height - 9.5 * cm
    c.drawString(2 * cm, client_y, f"Razão Social: {dados_cliente.get('razao_social', '')}")

    endereco = dados_cliente.get("endereco", "")
    cidade_uf_cep = dados_cliente.get("cidade_uf_cep", "")
    telefone = dados_cliente.get("telefone", "")

    if endereco:
        client_y -= 0.5 * cm
        c.drawString(2 * cm, client_y, f"Endereço: {endereco}")

    if cidade_uf_cep:
        client_y -= 0.5 * cm
        c.drawString(2 * cm, client_y, f"{cidade_uf_cep}")

    if telefone:
        client_y -= 0.5 * cm
        c.drawString(2 * cm, client_y, f"Telefone: {telefone}")

    client_y -= 0.5 * cm
    c.setLineWidth(0.5)
    c.line(1 * cm, client_y, width - 1 * cm, client_y)

    current_y = height - 13 * cm

    # Itens
    for i, item in enumerate(itens, start=1):
        if current_y < 5 * cm:
            c.showPage()
            page_number += 1
            draw_header(c, page_number)
            current_y = height - 7 * cm

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2 * cm, current_y, f"Item {i}")
        current_y -= 1 * cm

        c.setFont("Helvetica", 12)
        c.drawString(2 * cm, current_y, f"Produto: {item['produto']}")
        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, "Descrição:")
        current_y -= 0.5 * cm

        descricao_lines = wrap_text(item["descricao"], char_limit=80)
        c.setFont("Helvetica", 12)
        for line in descricao_lines:
            if current_y < 2.5 * cm:
                c.showPage()
                page_number += 1
                draw_header(c, page_number)
                current_y = height - 7 * cm
                c.setFont("Helvetica", 12)
            c.drawString(2 * cm, current_y, line)
            current_y -= 0.6 * cm

        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, f"Preço Unitário: R$ {item['preco_unitario']}")
        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, f"Quantidade: {item['quantidade']}")
        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, f"NCM: {item['ncm']}")
        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, f"Total: R$ {item['total']}")
        current_y -= 0.5 * cm
        c.drawString(2 * cm, current_y, f"Prazo de Entrega: {item['prazo_entrega']}")
        current_y -= 2 * cm

    # Nova página se necessário antes do resumo
    if current_y < 5 * cm:
        c.showPage()
        page_number += 1
        draw_header(c, page_number)
        current_y = height - 7 * cm

    # Total da cotação
    total_cotacao = sum(float(item["total"].replace(",", ".")) for item in itens)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(
        2 * cm,
        current_y,
        f"TOTAL DA COTAÇÃO: R$ {total_cotacao:.2f}".replace(".", ","),
    )
    current_y -= 1 * cm

    # Prazo de pagamento
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, current_y, f"Prazo de Pagamento: {prazo_pagamento}")
    current_y -= 1 * cm

    # Frete
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, current_y, f"Frete: {frete_tipo}")
    current_y -= 1 * cm

    # Rodapé da página atual
    footer_y_position = 1.5 * cm
    c.setLineWidth(0.5)
    c.line(1 * cm, footer_y_position + 0.5 * cm,
           width - 1 * cm, footer_y_position + 0.5 * cm)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, footer_y_position, footer_text)
    c.drawString(width - 5 * cm, footer_y_position, f"Página {page_number}")

    # Página de condições de fornecimento
    c.showPage()
    page_number += 1
    draw_header(c, page_number)
    current_y = height - 9 * cm

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, current_y, "Condições de fornecimento")
    current_y -= 1 * cm

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, current_y, "1. A cotação é válida por 5 dias.")
    current_y -= 1 * cm

    c.drawString(2 * cm, current_y, "2. O prazo de entrega está sujeito a alterações.")
    current_y -= 1 * cm

    c.drawString(
        2 * cm,
        current_y,
        "3. Se o item não estiver disponível para pronta entrega, ele será fabricado ou importado especificamente para",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "atender à sua necessidade. Nesses casos, não aceitamos devoluções ou cancelamentos de pedidos.",
    )
    current_y -= 1 * cm

    c.drawString(
        2 * cm,
        current_y,
        "4. Nossa empresa é optante pelo Simples Nacional, um regime tributário diferenciado e simplificado. Neste regime,",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "os impostos são pagos de forma unificada e estão todos inclusos no preço dos nossos produtos. Isso inclui tributos",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "federais, estaduais e municipais, como o Imposto de Renda, CSLL, PIS, COFINS, ICMS e ISS. Empresas que",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "compram nossos produtos para revenda ou industrialização podem gerar crédito de ICMS com uma alíquota de",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "aproximadamente 4%. Esse crédito pode ser usado para compensar o ICMS em operações futuras.",
    )
    current_y -= 1 * cm

    c.drawString(
        2 * cm,
        current_y,
        "5. Nos casos em que oferecemos um item similar ao originalmente solicitado pelo cliente, realizamos uma análise",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "técnica cuidadosa para garantir que o item proposto seja adequado. No entanto, é de responsabilidade exclusiva",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "do cliente realizar uma verificação detalhada e assegurar que o item proposto atenda plenamente às suas",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "necessidades específicas.",
    )
    current_y -= 1 * cm

    c.drawString(
        2 * cm,
        current_y,
        "6. O faturamento a prazo está sujeito a uma análise financeira, a qual será realizada somente após o recebimento",
    )
    current_y -= 0.5 * cm
    c.drawString(
        2 * cm,
        current_y,
        "do pedido de compra.",
    )

    footer_y_position = 1.5 * cm
    c.setLineWidth(0.5)
    c.line(1 * cm, footer_y_position + 0.5 * cm,
           width - 1 * cm, footer_y_position + 0.5 * cm)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, footer_y_position, footer_text)
    c.drawString(width - 5 * cm, footer_y_position, f"Página {page_number}")

    c.save()
