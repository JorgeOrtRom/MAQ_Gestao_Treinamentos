import datetime as dt_module
from datetime import datetime
import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
from reportlab.graphics.shapes import Circle, Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import streamlit as st
from supabase import Client, create_client

# Configuração da página corporativa
st.set_page_config(
    page_title="Sistema Enterprise de Gestão de Treinamentos - MAQ",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded",
)

# Estilização CSS Original
st.markdown(
    """
<style>
    .main-header {
        font-size: 24px;
        font-weight: bold;
        color: #0F172A;
        padding-bottom: 10px;
        border-bottom: 2px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .colab-card {
        background-color: #F8FAFC;
        border-left: 6px solid #2563EB;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


def limpar_valor(val):
  if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", ""]:
    return None
  return str(val).strip()


# -------------------------------------------------------------------
# CONEXÃO COM O SUPABASE CLOUD
# -------------------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
  try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
  except Exception:
    url = "https://seu-projeto.supabase.co"
    key = "sua-chave-aqui"
  return create_client(url, key)


supabase = init_supabase()


def carregar_logo_empresa():
  nomes_possiveis = [
      "Logo_Attend_ Ambiental.png",
      "Logo_Attend_ Ambiental.jpg",
      "Logo_Attend_ Ambiental.jpeg",
      "Logo_Attend_Ambiental.png",
      "Logo_Attend_Ambiental.jpg",
      "logo.png",
  ]
  for nome in nomes_possiveis:
    if os.path.exists(nome):
      return nome
  return None


def get_lista_departamentos():
  try:
    res = (
        supabase.table("colaboradores")
        .select("departamento")
        .neq("departamento", "")
        .execute()
    )
    df_deptos = pd.DataFrame(res.data)
    if not df_deptos.empty:
      return sorted(df_deptos["departamento"].unique().tolist())
  except Exception:
    pass
  return [
      "EXECUÇÃO",
      "MANUTENÇÃO",
      "OPERAÇÃO",
      "ALMOXARIFE",
      "ADMINISTRATIVO",
      "SEGURANÇA (SSO)",
  ]


def registrar_log(usuario, acao, detalhes):
  try:
    supabase.table("logs_auditoria").insert({
        "usuario": str(usuario),
        "acao": str(acao),
        "detalhes": str(detalhes),
    }).execute()
  except Exception:
    pass


# -------------------------------------------------------------------
# AUTENTICAÇÃO E PERFIS DE ACESSO
# -------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None
if "perfil_usuario" not in st.session_state:
  st.session_state["perfil_usuario"] = None
if "nome_usuario" not in st.session_state:
  st.session_state["nome_usuario"] = None
if "pagina" not in st.session_state:
  st.session_state["pagina"] = "📊 Dashboard Executivo"

# TELA DE LOGIN
if st.session_state["usuario_logado"] is None:
  st.markdown("<br><br>", unsafe_allow_html=True)
  c_center1, c_center2, c_center3 = st.columns([1, 2, 1])

  with c_center2:
    logo_caminho = carregar_logo_empresa()
    if logo_caminho:
      st.image(logo_caminho, width=220)
    else:
      st.image(
          "https://img.icons8.com/color/96/verified-badge.png", width=70
      )

    st.title("Gestão MAQ")
    st.caption("🔒 Acesso Restrito ao Sistema de Compliance e Treinamentos")

    with st.form("form_login"):
      user_input = st.text_input("Usuário / Login")
      pass_input = st.text_input("Senha", type="password")
      btn_login = st.form_submit_button(
          "🔑 Entrar no Sistema", use_container_width=True
      )

      if btn_login:
        try:
          res = (
              supabase.table("usuarios")
              .select("login, nome, perfil")
              .eq("login", user_input.strip())
              .eq("senha", pass_input.strip())
              .execute()
          )
          if res.data:
            u = res.data[0]
            st.session_state["usuario_logado"] = u["login"]
            st.session_state["nome_usuario"] = u["nome"]
            st.session_state["perfil_usuario"] = u["perfil"]
            registrar_log(
                u["nome"],
                "LOGIN",
                f"Usuário {u['login']} efetuou login com perfil {u['perfil']}",
            )
            st.success(f"Bem-vindo(a), {u['nome']}!")
            st.rerun()
          else:
            st.error("❌ Usuário ou senha incorretos.")
        except Exception as e:
          st.error(f"Erro ao conectar ao Supabase: {e}")

    st.info(
        "💡 **Acesso Padrão:** Admin: `admin` / `admin123` | Auditor:"
        " `auditor` / `auditor123` | Gestor: `gestor` / `gestor123`"
    )
  st.stop()

# -------------------------------------------------------------------
# MENU LATERAL - NAVEGAÇÃO
# -------------------------------------------------------------------
with st.sidebar:
  logo_caminho = carregar_logo_empresa()
  if logo_caminho:
    st.image(logo_caminho, use_container_width=True)
  else:
    st.image("https://img.icons8.com/color/96/verified-badge.png", width=50)

  st.title("MAQ Gestão")

  perfil = st.session_state["perfil_usuario"]
  nome_u = st.session_state["nome_usuario"]

  st.markdown(f"👤 **{nome_u}**\n\n🛡️ *Perfil: {perfil}*")

  if st.button("🚪 Sair (Logout)", use_container_width=True):
    registrar_log(nome_u, "LOGOUT", "Sessão encerrada.")
    st.session_state["usuario_logado"] = None
    st.session_state["perfil_usuario"] = None
    st.rerun()

  ano_atual = dt_module.date.today().year
  anos_disponiveis = [ano_atual - 1, ano_atual, ano_atual + 1]
  ano_exercicio = st.selectbox(
      "📅 Exercício Anual do Sistema:", anos_disponiveis, index=1
  )

  st.divider()

  opcoes = [
      "📊 Dashboard Executivo",
      "👤 Visão do Colaborador",
      "📈 Evolução por Treinamento",
  ]

  if perfil in ["Admin", "Gestor"]:
    opcoes.extend(["✍️ Lançar Treinamento", "📜 Certificados & Presença"])

  opcoes.append("📂 Relatórios p/ Auditoria")

  if perfil == "Admin":
    opcoes.extend([
        "👥 Gestão de Colaboradores",
        "📚 Catálogo de Treinamentos",
        "🎯 Matriz por Cargo (LNT)",
        "🔑 Gestão de Usuários",
        "💰 Gestão Orçamentária",
        "📜 Logs de Auditoria",
    ])
  elif perfil == "Auditor":
    opcoes.extend(["📜 Logs de Auditoria", "📚 Catálogo de Treinamentos"])

  for opt in opcoes:
    if st.button(opt, use_container_width=True, key=f"btn_nav_{opt}"):
      st.session_state["pagina"] = opt
      st.rerun()

pagina = st.session_state["pagina"]


# -------------------------------------------------------------------
# GERADORES DE PDF E SUPABASE STORAGE
# -------------------------------------------------------------------
def criar_selo_oficial():
  d = Drawing(85, 85)
  d.add(
      Circle(
          42,
          42,
          38,
          fillColor=colors.HexColor("#D97706"),
          strokeColor=colors.HexColor("#B45309"),
          strokeWidth=2,
      )
  )
  d.add(
      Circle(
          42,
          42,
          31,
          fillColor=colors.HexColor("#0F172A"),
          strokeColor=colors.HexColor("#F59E0B"),
          strokeWidth=1.5,
      )
  )
  d.add(
      String(
          42,
          39,
          "OFICIAL",
          textAnchor="middle",
          fontName="Helvetica-Bold",
          fontSize=9,
          fillColor=colors.white,
      )
  )
  d.add(
      String(
          42,
          51,
          "★ ★ ★",
          textAnchor="middle",
          fontName="Helvetica-Bold",
          fontSize=8,
          fillColor=colors.HexColor("#F59E0B"),
      )
  )
  d.add(
      String(
          42,
          28,
          "COMPLIANCE",
          textAnchor="middle",
          fontName="Helvetica-Bold",
          fontSize=6,
          fillColor=colors.HexColor("#F59E0B"),
      )
  )
  return d


def desenhar_moldura_certificado(canvas, doc):
  canvas.saveState()
  canvas.setStrokeColor(colors.HexColor("#0F172A"))
  canvas.setLineWidth(4)
  canvas.rect(20, 20, doc.pagesize[0] - 40, doc.pagesize[1] - 40)
  canvas.setStrokeColor(colors.HexColor("#D97706"))
  canvas.setLineWidth(1.5)
  canvas.rect(26, 26, doc.pagesize[0] - 52, doc.pagesize[1] - 52)
  canvas.restoreState()


def gerar_pdf_prontuario(colab_info, df_realizados, total_mapeados, ano):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  story = []
  styles = getSampleStyleSheet()

  logo_file = carregar_logo_empresa()
  if logo_file:
    try:
      img = Image(logo_file, width=140, height=45)
      img.hAlign = "CENTER"
      story.append(img)
      story.append(Spacer(1, 10))
    except Exception:
      pass

  story.append(
      Paragraph(
          "<b>SISTEMA DE GESTÃO DE TREINAMENTOS - MAQ</b>",
          ParagraphStyle(
              "TitleStyle",
              parent=styles["Heading1"],
              fontSize=16,
              leading=20,
              textColor=colors.HexColor("#0F172A"),
              alignment=1,
          ),
      )
  )
  story.append(
      Paragraph(
          f"Prontuário Individual de Capacitação - Exercício {ano}",
          ParagraphStyle(
              "SubTitleStyle",
              parent=styles["Normal"],
              fontSize=10,
              leading=12,
              textColor=colors.HexColor("#64748B"),
              alignment=1,
          ),
      )
  )
  story.append(Spacer(1, 15))

  dados_colab = [
      [
          Paragraph(
              f"<b>Nome:</b> {colab_info['nome']}", styles["Normal"]
          ),
          Paragraph(
              f"<b>Cargo:</b> {colab_info['cargo'] or 'N/A'}",
              styles["Normal"],
          ),
      ],
      [
          Paragraph(
              f"<b>Departamento:</b> {colab_info['departamento']}",
              styles["Normal"],
          ),
          Paragraph(
              f"<b>Gestor:</b> {colab_info['gestor'] or 'N/A'}",
              styles["Normal"],
          ),
      ],
      [
          Paragraph(
              f"<b>E-mail:</b> {colab_info['email'] or 'N/A'}", styles["Normal"]
          ),
          Paragraph(
              "<b>Data Emissão:</b>"
              f" {dt_module.date.today().strftime('%d/%m/%Y')}",
              styles["Normal"],
          ),
      ],
  ]
  t_info = Table(dados_colab, colWidths=[270, 270])
  t_info.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
          ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
          ("PADDING", (0, 0), (-1, -1), 6),
      ])
  )
  story.append(t_info)
  story.append(Spacer(1, 15))

  story.append(
      Paragraph(
          "<b>HISTÓRICO DE TREINAMENTOS CUMPRIDOS NO EXERCÍCIO</b>",
          ParagraphStyle(
              "NormalBold",
              parent=styles["Normal"],
              fontSize=10,
              leading=12,
              fontName="Helvetica-Bold",
          ),
      )
  )
  story.append(Spacer(1, 5))

  headers = [
      "Treinamento / Norma",
      "Carga Horária",
      "Data Realização",
      "Validade",
      "Status",
  ]
  table_data = [
      [Paragraph(f"<b>{h}</b>", styles["Normal"]) for h in headers]
  ]

  if not df_realizados.empty:
    for _, r in df_realizados.iterrows():
      dt_r = pd.to_datetime(r["DataRealizacao"]).strftime("%d/%m/%Y")
      dt_v = (
          pd.to_datetime(r["DataRealizacao"])
          + pd.DateOffset(months=r["ValidadeMeses"])
      ).strftime("%d/%m/%Y")
      table_data.append([
          Paragraph(str(r["Treinamento"]), styles["Normal"]),
          Paragraph(f"{r['Horas']}h", styles["Normal"]),
          Paragraph(dt_r, styles["Normal"]),
          Paragraph(dt_v, styles["Normal"]),
          Paragraph("CONFORME", styles["Normal"]),
      ])
  else:
    table_data.append([
        Paragraph(
            "Nenhum registro encontrado para este ano.", styles["Normal"]
        ),
        "",
        "",
        "",
        "",
    ])

  t_treinos = Table(table_data, colWidths=[200, 70, 90, 90, 90])
  t_treinos.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
          ("PADDING", (0, 0), (-1, -1), 5),
      ])
  )
  story.append(t_treinos)
  story.append(Spacer(1, 30))
  story.append(
      Paragraph(
          "___________________________________"
          " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
          " ___________________________________",
          styles["Normal"],
      )
  )
  story.append(
      Paragraph(
          "Assinatura do Colaborador"
          " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
          " Assinatura do Responsável RH",
          styles["Normal"],
      )
  )

  doc.build(story)
  buffer.seek(0)
  return buffer


def gerar_pdf_certificado(
    colab_nome,
    colab_cargo,
    curso_nome,
    carga_horaria,
    data_realizacao,
    aplicador_nome="Aplicador Técnico",
    aplicador_cargo="Aplicador do Treinamento",
):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=landscape(letter),
      rightMargin=45,
      leftMargin=45,
      topMargin=40,
      bottomMargin=35,
  )
  story = []
  styles = getSampleStyleSheet()

  logo_file = carregar_logo_empresa()
  selo = criar_selo_oficial()

  if logo_file:
    try:
      img_logo = Image(logo_file, width=180, height=55)
      t_top = Table([[img_logo, selo]], colWidths=[530, 150])
    except Exception:
      t_top = Table([["", selo]], colWidths=[530, 150])
  else:
    t_top = Table([["", selo]], colWidths=[530, 150])

  t_top.setStyle(
      TableStyle([
          ("ALIGN", (0, 0), (0, 0), "LEFT"),
          ("ALIGN", (1, 0), (1, 0), "RIGHT"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
      ])
  )
  story.append(t_top)
  story.append(Spacer(1, 15))

  title_main = ParagraphStyle(
      "CertMain",
      parent=styles["Heading1"],
      fontSize=34,
      leading=38,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#0F172A"),
      alignment=1,
  )
  story.append(Paragraph("CERTIFICADO DE CONCLUSÃO", title_main))
  story.append(Spacer(1, 15))

  sub_title_style = ParagraphStyle(
      "CertSubTitle",
      parent=styles["Normal"],
      fontSize=13,
      leading=16,
      fontName="Helvetica-Oblique",
      textColor=colors.HexColor("#475569"),
      alignment=1,
  )
  story.append(Paragraph("confere o presente certificado a", sub_title_style))
  story.append(Spacer(1, 12))

  nome_style = ParagraphStyle(
      "CertNome",
      parent=styles["Heading1"],
      fontSize=28,
      leading=32,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#1E3A8A"),
      alignment=1,
  )
  story.append(Paragraph(f"{str(colab_nome).upper()}", nome_style))
  story.append(Spacer(1, 15))

  dt_f = pd.to_datetime(data_realizacao).strftime("%d/%m/%Y")
  desc_text = (
      f"pela conclusão com êxito do treinamento de <b>{curso_nome}</b>,"
      f" realizado em <b>{dt_f}</b>, com carga horária total de <b>{carga_horaria}"
      " horas</b>, em conformidade com as normas de segurança e gestão da"
      " Attend Ambiental."
  )
  desc_style = ParagraphStyle(
      "CertDesc",
      parent=styles["Normal"],
      fontSize=11.5,
      leading=17,
      textColor=colors.HexColor("#334155"),
      alignment=1,
  )
  story.append(Paragraph(desc_text, desc_style))
  story.append(Spacer(1, 35))

  ass_nome_style = ParagraphStyle(
      "AssNome",
      parent=styles["Normal"],
      fontSize=9.5,
      leading=11,
      fontName="Helvetica-Bold",
      textColor=colors.HexColor("#0F172A"),
      alignment=1,
  )
  ass_cargo_style = ParagraphStyle(
      "AssCargo",
      parent=styles["Normal"],
      fontSize=8,
      leading=10,
      textColor=colors.HexColor("#64748B"),
      alignment=1,
  )

  colab_cargo_txt = colab_cargo if colab_cargo else "Analista"
  ap_nome_txt = aplicador_nome if aplicador_nome else "Aplicador Técnico"
  ap_cargo_txt = (
      aplicador_cargo if aplicador_cargo else "Aplicador do Treinamento"
  )

  linha = Paragraph("___________________________________", ass_cargo_style)

  dados_ass = [
      [linha, linha, linha],
      [
          Paragraph(f"<b>{ap_nome_txt}</b>", ass_nome_style),
          Paragraph("<b>Jéssica Rocha</b>", ass_nome_style),
          Paragraph(f"<b>{colab_nome}</b>", ass_nome_style),
      ],
      [
          Paragraph(f"{ap_cargo_txt}", ass_cargo_style),
          Paragraph("Gestora de MAQ / SSO", ass_cargo_style),
          Paragraph(f"{colab_cargo_txt}", ass_cargo_style),
      ],
  ]

  t_ass = Table(dados_ass, colWidths=[225, 230, 225])
  t_ass.setStyle(
      TableStyle([
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("PADDING", (0, 0), (-1, -1), 2),
      ])
  )
  story.append(t_ass)

  doc.build(story, onFirstPage=desenhar_moldura_certificado)
  buffer.seek(0)
  return buffer


def gerar_pdf_lista_presenca(
    curso_nome, carga_horaria, departamento_nome, lista_colabs, ano
):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  story = []
  styles = getSampleStyleSheet()
  sub_style = ParagraphStyle(
      "LPSub",
      parent=styles["Normal"],
      fontSize=10,
      leading=12,
      textColor=colors.HexColor("#475569"),
  )

  logo_file = carregar_logo_empresa()
  if logo_file:
    try:
      img = Image(logo_file, width=140, height=45)
      img.hAlign = "CENTER"
      story.append(img)
      story.append(Spacer(1, 10))
    except Exception:
      pass

  story.append(
      Paragraph(
          f"<b>LISTA DE PRESENÇA OFICIAL DE TREINAMENTO ({ano}) - MAQ</b>",
          ParagraphStyle(
              "LPTitle",
              parent=styles["Heading1"],
              fontSize=16,
              leading=20,
              textColor=colors.HexColor("#0F172A"),
              alignment=1,
          ),
      )
  )
  story.append(Spacer(1, 10))

  header_data = [
      [
          Paragraph(f"<b>Treinamento:</b> {curso_nome}", sub_style),
          Paragraph(f"<b>Carga Horária:</b> {carga_horaria}h", sub_style),
      ],
      [
          Paragraph(
              f"<b>Setor/Departamento:</b> {departamento_nome}", sub_style
          ),
          Paragraph(f"<b>Data de Aplicação:</b> ____/____/{ano}", sub_style),
      ],
      [
          Paragraph(
              "<b>Gestora responsável MAQ:</b> Jéssica Rocha", sub_style
          ),
          Paragraph("<b>Aplicador:</b> ________________________", sub_style),
      ],
  ]
  t_head = Table(header_data, colWidths=[270, 270])
  t_head.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
          ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
          ("PADDING", (0, 0), (-1, -1), 5),
      ])
  )
  story.append(t_head)
  story.append(Spacer(1, 15))

  headers = [
      "#",
      "Nome do Colaborador",
      "Cargo / Função",
      "Assinatura do Participante",
  ]
  table_rows = [[Paragraph(f"<b>{h}</b>", sub_style) for h in headers]]

  for idx, c in enumerate(lista_colabs, start=1):
    table_rows.append([
        Paragraph(str(idx), sub_style),
        Paragraph(str(c["nome"]), sub_style),
        Paragraph(str(c["cargo"] or "Operacional"), sub_style),
        Paragraph("", sub_style),
    ])

  t_list = Table(table_rows, colWidths=[30, 200, 130, 180])
  t_list.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
          ("PADDING", (0, 0), (-1, -1), 6),
      ])
  )
  story.append(t_list)
  story.append(Spacer(1, 20))
  story.append(
      Paragraph(
          "<b>Visto da Gestão MAQ (Jéssica Rocha):</b>"
          " ___________________________ &nbsp;&nbsp;&nbsp;&nbsp;"
          f" <b>Data:</b> ____/____/{ano}",
          sub_style,
      )
  )

  doc.build(story)
  buffer.seek(0)
  return buffer


def salvar_arquivo_supabase(
    path_name, bytes_data, content_type="application/pdf"
):
  try:
    supabase.storage.from_("evidencias").upload(
        path=path_name,
        file=bytes_data,
        file_options={"content-type": content_type, "upsert": "true"},
    )
    return path_name
  except Exception:
    return path_name


def deletar_arquivo_supabase(path_name):
  try:
    if path_name and str(path_name).strip().lower() not in [
        "none",
        "nan",
        "sem anexo",
        "",
    ]:
      supabase.storage.from_("evidencias").remove([path_name])
  except Exception:
    pass


def baixar_arquivo_supabase(path_name):
  try:
    res = supabase.storage.from_("evidencias").download(path_name)
    return res
  except Exception:
    return None


# -------------------------------------------------------------------
# 1. DASHBOARD EXECUTIVO
# -------------------------------------------------------------------
if pagina == "📊 Dashboard Executivo":
  st.markdown(
      '<div class="main-header">📊 Dashboard Geral de Performance e Compliance'
      f" Executivo ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )

  try:
    res_reg = (
        supabase.table("registros")
        .select(
            "data_realizacao, validade_meses, status_planilha, colaboradores(nome, departamento),"
            " treinamentos(nome_curso, carga_horaria, classificacao)"
        )
        .execute()
    )
  except Exception:
    res_reg = type("obj", (object,), {"data": []})()

  res_colabs_count = (
      supabase.table("colaboradores").select("id", count="exact").execute()
  )
  df_colabs_total = res_colabs_count.count or 0

  if not res_reg.data:
    st.info(
        "💡 Nenhum registro cadastrado no banco de dados para o ano de"
        f" {ano_exercicio}."
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("👥 Colaboradores", df_colabs_total)
    k2.metric("⏱️ Horas Capacitadas", "0.0h")
    k3.metric("📈 Taxa Conformidade", "0.0%")
    k4.metric("🟢 Em Dia", 0)
    k5.metric("🔴 Vencidos", 0)
  else:
    flat_data = []
    for r in res_reg.data:
      dt_r = r.get("data_realizacao")
      colab = r.get("colaboradores") or {}
      treino = r.get("treinamentos") or {}
      status_db = r.get("status_planilha")

      if status_db == "Concluído" and dt_r and str(dt_r).startswith(str(ano_exercicio)):
        flat_data.append({
            "Colaborador": colab.get("nome", "Desconhecido"),
            "Departamento": colab.get("departamento", "Geral"),
            "Treinamento": treino.get("nome_curso", "Geral"),
            "Horas": float(treino.get("carga_horaria") or 0),
            "Classificacao": treino.get("classificacao", "Geral"),
            "DataRealizacao": dt_r,
            "ValidadeMeses": int(r.get("validade_meses") or 12),
        })

    df = pd.DataFrame(flat_data)

    if df.empty:
      st.info(
          f"💡 Nenhum registro encontrado para o exercício {ano_exercicio}."
      )
      k1, k2, k3, k4, k5 = st.columns(5)
      k1.metric("👥 Colaboradores", df_colabs_total)
      k2.metric("⏱️ Horas Capacitadas", "0.0h")
      k3.metric("📈 Taxa Conformidade", "0.0%")
      k4.metric("🟢 Em Dia", 0)
      k5.metric("🔴 Vencidos", 0)
    else:
      df["DataRealizacao"] = pd.to_datetime(df["DataRealizacao"])
      df["DataVencimento"] = df.apply(
          lambda row: row["DataRealizacao"]
          + pd.DateOffset(months=row["ValidadeMeses"]),
          axis=1,
      )
      hoje = pd.to_datetime(dt_module.date.today())
      df["DiasParaVencer"] = (df["DataVencimento"] - hoje).dt.days

      def set_status(dias):
        if dias < 0:
          return "🔴 Vencido (Não Conforme)"
        elif dias <= 30:
          return "🟡 Vencerá em 30 Dias"
        else:
          return "🟢 Conforme / Em Dia"

      df["Status"] = df["DiasParaVencer"].apply(set_status)

      c1, c2, c3 = st.columns(3)
      with c1:
        depto_sel = st.multiselect(
            "Filtrar Departamento",
            options=df["Departamento"].unique(),
            default=df["Departamento"].unique(),
        )
      with c2:
        classif_sel = st.multiselect(
            "Filtrar Classificação",
            options=df["Classificacao"].unique(),
            default=df["Classificacao"].unique(),
        )
      with c3:
        status_sel = st.multiselect(
            "Filtrar Status",
            options=df["Status"].unique(),
            default=df["Status"].unique(),
        )

      df_filtered = df[
          (df["Departamento"].isin(depto_sel))
          & (df["Classificacao"].isin(classif_sel))
          & (df["Status"].isin(status_sel))
      ]

      st.divider()
      k1, k2, k3, k4, k5 = st.columns(5)
      total_horas = df_filtered["Horas"].sum()
      conformes = len(
          df_filtered[df_filtered["Status"] == "🟢 Conforme / Em Dia"]
      )
      nao_conformes = len(
          df_filtered[df_filtered["Status"] == "🔴 Vencido (Não Conforme)"]
      )
      tx_conformidade = (
          (conformes / len(df_filtered) * 100) if len(df_filtered) > 0 else 0.0
      )

      k1.metric("👥 Colaboradores", df_colabs_total)
      k2.metric("⏱ Horas Capacitadas", f"{total_horas:.1f}h")
      k3.metric("📈 Taxa Conformidade", f"{tx_conformidade:.1f}%")
      k4.metric("🟢 Em Dia", conformes)
      k5.metric("🔴 Vencidos", nao_conformes, delta_color="inverse")

      st.divider()
      col_g1, col_g2 = st.columns(2)
      with col_g1:
        st.subheader("📊 Compliance por Status")
        fig_status = px.pie(
            df_filtered,
            names="Status",
            hole=0.4,
            color="Status",
            color_discrete_map={
                "🟢 Conforme / Em Dia": "#10B981",
                "🟡 Vencerá em 30 Dias": "#F59E0B",
                "🔴 Vencido (Não Conforme)": "#EF4444",
            },
        )
        st.plotly_chart(fig_status, use_container_width=True)
      with col_g2:
        st.subheader(
            f"🏢 Horas Capacitadas em {ano_exercicio} por Setor"
        )
        df_depto = (
            df_filtered.groupby("Departamento")["Horas"].sum().reset_index()
        )
        fig_bar = px.bar(
            df_depto,
            x="Departamento",
            y="Horas",
            text_auto=".1f",
            color="Departamento",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------------
# 2. VISÃO DO COLABORADOR (COM TABELA INTERATIVA ST.DATA_EDITOR)
# -------------------------------------------------------------------
elif pagina == "👤 Visão do Colaborador":
  st.markdown(
      '<div class="main-header">👤 Prontuário Individual e Matriz de'
      f" Participação ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )

  res_c = supabase.table("colaboradores").select("*").order("nome").execute()
  df_colabs = pd.DataFrame(res_c.data)

  if df_colabs.empty:
    st.warning("Nenhum colaborador cadastrado.")
  else:
    colab_nome = st.selectbox(
        "🔎 Selecione o Colaborador:", df_colabs["nome"].tolist()
    )
    colab_info = df_colabs[df_colabs["nome"] == colab_nome].iloc[0]
    cid = int(colab_info["id"])

    res_lnt = (
        supabase.table("matriz_cargo_treinamento")
        .select("treinamento_id, treinamentos(*)")
        .eq("cargo", colab_info["cargo"])
        .execute()
    )
    if res_lnt.data:
      df_lnt_cargo = pd.DataFrame([r["treinamentos"] for r in res_lnt.data])
    else:
      res_all_t = supabase.table("treinamentos").select("*").execute()
      df_lnt_cargo = pd.DataFrame(res_all_t.data)

    total_mapeados = len(df_lnt_cargo)

    res_ind = (
        supabase.table("registros")
        .select("*, treinamentos(*)")
        .eq("colaborador_id", cid)
        .execute()
    )
    flat_ind = []
    if res_ind.data:
      for r in res_ind.data:
        flat_ind.append({
            "ID": r.get("id"),
            "TreinamentoID": r["treinamento_id"],
            "Treinamento": (
                r["treinamentos"]["nome_curso"] if r.get("treinamentos") else ""
            ),
            "Classificacao": (
                r["treinamentos"]["classificacao"]
                if r.get("treinamentos")
                else ""
            ),
            "Horas": float(
                r["treinamentos"]["carga_horaria"]
                if r.get("treinamentos")
                else 0
            ),
            "DataRealizacao": r.get("data_realizacao"),
            "ValidadeMeses": int(r.get("validade_meses") or 12),
            "Evidencia": r.get("arquivo_evidencia"),
            "Forms": r.get("arquivo_forms"),
            "Instrutor": r.get("instrutor_nome"),
            "AplicadorCargo": r.get("aplicador_cargo"),
            "StatusPlanilha": r.get("status_planilha"),
        })
    df_realizados = pd.DataFrame(flat_ind)

    df_concluidos = (
        df_realizados[df_realizados["StatusPlanilha"] == "Concluído"]
        if not df_realizados.empty
        else pd.DataFrame()
    )
    qtd_realizados = len(df_concluidos)
    qtd_pendentes = max(0, total_mapeados - qtd_realizados)
    pct_concluido = (
        (qtd_realizados / total_mapeados * 100) if total_mapeados > 0 else 0.0
    )
    horas_acumuladas = (
        df_concluidos["Horas"].sum() if not df_concluidos.empty else 0.0
    )

    c_f1, c_f2 = st.columns([3, 1])
    with c_f1:
      st.markdown(
          f"""
            <div class="colab-card">
                <h3 style="margin-top:0;">👤 <b>{colab_info['nome']}</b></h3>
                <p style="margin-bottom:5px;">💼 <b>Cargo:</b> {colab_info['cargo'] or 'Não informado'} &nbsp;|&nbsp; 👔 <b>Gestor Direto:</b> {colab_info['gestor'] or 'Não informado'}</p>
                <p style="margin-bottom:0;">🏢 <b>Departamento:</b> {colab_info['departamento']} &nbsp;|&nbsp; ✉️ <b>E-mail:</b> {colab_info['email'] or 'N/A'}</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with c_f2:
      st.write(f"📄 **Prontuário {ano_exercicio}**")
      pdf_bytes = gerar_pdf_prontuario(
          colab_info, df_concluidos, total_mapeados, ano_exercicio
      )
      st.download_button(
          label="🖨️ Baixar Prontuário PDF",
          data=pdf_bytes,
          file_name=(
              f"Prontuario_{colab_info['nome'].replace(' ', '_')}_{ano_exercicio}.pdf"
          ),
          mime="application/pdf",
          use_container_width=True,
      )

    st.subheader(
        f"📊 Evolução de Treinamentos Mapeados ({ano_exercicio})"
    )
    st.write(
        f"**Progresso:** `{qtd_realizados}` de `{total_mapeados}` cursos exigidos"
        f" concluídos em {ano_exercicio} (**{pct_concluido:.1f}%**)"
    )
    st.progress(min(pct_concluido / 100.0, 1.0))

    kc1, kc2, k3, kc4 = st.columns(4)
    kc1.metric("🎯 Exigidos p/ Cargo", f"{total_mapeados} Cursos")
    kc2.metric("✅ Concluídos no Ano", f"{qtd_realizados} Cursos")
    k3.metric("⏳ Pendentes no Ano", f"{qtd_pendentes} Cursos")
    kc4.metric("⏱ Horas Cumpridas", f"{horas_acumuladas:.1f}h")

    st.divider()
    st.subheader("📋 Matriz e Status de Treinamentos (Grade Editável)")

    # Monta a tabela unificada para o data_editor
    matriz_rows = []
    for _, r_t in df_lnt_cargo.iterrows():
      tid = int(r_t["id"])
      reg_match = (
          df_realizados[df_realizados["TreinamentoID"] == tid]
          if not df_realizados.empty
          else pd.DataFrame()
      )
      is_concluido = not reg_match.empty and (
          reg_match.iloc[0].get("StatusPlanilha") == "Concluído"
      )
      reg_info = reg_match.iloc[0] if not reg_match.empty else None

      dt_real = (
          reg_info["DataRealizacao"]
          if is_concluido and reg_info["DataRealizacao"]
          else dt_module.date.today().strftime("%Y-%m-%d")
      )
      inst_real = (
          reg_info["Instrutor"]
          if (is_concluido and reg_info["Instrutor"])
          else (r_t.get("aplicador_padrao") or "Aplicador Técnico")
      )
      cargo_ap_real = (
          reg_info["AplicadorCargo"]
          if (is_concluido and reg_info.get("AplicadorCargo"))
          else (
              r_t.get("aplicador_cargo_padrao") or "Aplicador do Treinamento"
          )
      )

      matriz_rows.append({
          "TreinamentoID": tid,
          "Treinamento": r_t["nome_curso"],
          "Carga Horária": f"{r_t['carga_horaria']}h",
          "Concluído": is_concluido,
          "Data Aplicação": dt_real,
          "Nome Aplicador": inst_real or "",
          "Cargo Aplicador": cargo_ap_real or "",
          "Certificado Atual": reg_info["Evidencia"] if is_concluido else "-",
      })

    df_editor_base = pd.DataFrame(matriz_rows)

    df_editado = st.data_editor(
        df_editor_base,
        column_config={
            "TreinamentoID": None,
            "Treinamento": st.column_config.TextColumn(
                "Treinamento / Norma", disabled=True
            ),
            "Carga Horária": st.column_config.TextColumn("CH", disabled=True),
            "Concluído": st.column_config.CheckboxColumn("Concluído?"),
            "Data Aplicação": st.column_config.DateColumn("Data Aplicação"),
            "Nome Aplicador": st.column_config.TextColumn("Nome Aplicador"),
            "Cargo Aplicador": st.column_config.TextColumn("Cargo Aplicador"),
            "Certificado Atual": st.column_config.TextColumn(
                "Certificado Arquivado", disabled=True
            ),
        },
        disabled=["TreinamentoID", "Treinamento", "Carga Horária", "Certificado Atual"],
        hide_index=True,
        use_container_width=True,
        key=f"editor_matriz_{cid}",
    )

    if st.button("💾 Salvar Alterações na Matriz", type="primary", use_container_width=True):
      try:
        for idx, row in df_editado.iterrows():
          tid = int(row["TreinamentoID"])
          status_marcado = row["Concluído"]
          dt_real_str = str(row["Data Aplicação"])[:10]
          nome_ap = row["Nome Aplicador"]
          cargo_ap = row["Cargo Aplicador"]
          nome_curso = row["Treinamento"]
          ch_val = row["Carga Horária"].replace("h", "")

          # Consulta o estado atual no Supabase
          check_db = (
              supabase.table("registros")
              .select("id, arquivo_evidencia, arquivo_forms")
              .eq("colaborador_id", cid)
              .eq("treinamento_id", tid)
              .execute()
          )

          if status_marcado:
            # Gera Certificado PDF
            nome_cert_auto = f"Certificado_AUTO_{cid}_{tid}_{dt_real_str}.pdf"
            pdf_bytes_cert = gerar_pdf_certificado(
                colab_nome=str(colab_info["nome"]),
                colab_cargo=str(colab_info["cargo"] or ""),
                curso_nome=str(nome_curso),
                carga_horaria=str(ch_val),
                data_realizacao=dt_real_str,
                aplicador_nome=limpar_valor(nome_ap) or "Aplicador Técnico",
                aplicador_cargo=limpar_valor(cargo_ap)
                or "Aplicador do Treinamento",
            )
            salvar_arquivo_supabase(
                nome_cert_auto, pdf_bytes_cert.getvalue()
            )

            payload = {
                "colaborador_id": cid,
                "treinamento_id": tid,
                "data_realizacao": dt_real_str,
                "validade_meses": 12,
                "status_planilha": "Concluído",
                "arquivo_evidencia": nome_cert_auto,
                "arquivo_forms": "Sem anexo",
                "instrutor_nome": limpar_valor(nome_ap),
                "aplicador_cargo": limpar_valor(cargo_ap),
                "custo_real": 0.0,
            }

            if check_db.data:
              supabase.table("registros").update(payload).eq(
                  "id", check_db.data[0]["id"]
              ).execute()
            else:
              supabase.table("registros").insert(payload).execute()

          else:
            # Se foi desmarcado, remove do banco e do Storage
            if check_db.data:
              r_del = check_db.data[0]
              deletar_arquivo_supabase(r_del.get("arquivo_evidencia"))
              deletar_arquivo_supabase(r_del.get("arquivo_forms"))
              supabase.table("registros").delete().eq(
                  "id", r_del["id"]
              ).execute()

        st.cache_data.clear()
        st.success("🎉 Alterações salvas com sucesso no banco de dados!")
        st.rerun()

      except Exception as err:
        st.error(f"Erro ao salvar alterações: {err}")

# -------------------------------------------------------------------
# 3. LANÇAR TREINAMENTO
# -------------------------------------------------------------------
elif pagina == "✍️ Lançar Treinamento":
  st.markdown(
      '<div class="main-header">✍️ Registro de Treinamento e Emissão'
      " Automática de Certificado</div>",
      unsafe_allow_html=True,
  )

  res_c = supabase.table("colaboradores").select("*").order("nome").execute()
  res_t = supabase.table("treinamentos").select("*").order("nome_curso").execute()

  df_colab = pd.DataFrame(res_c.data)
  df_treino = pd.DataFrame(res_t.data)

  if df_colab.empty or df_treino.empty:
    st.warning("Cadastre colaboradores e treinamentos antes.")
  else:
    with st.form("form_registro_evidencia"):
      c1, c2 = st.columns(2)
      with c1:
        colab_dict = {
            f"{r['nome']} ({r['departamento']})": (
                r["id"],
                r["nome"],
                r["cargo"],
            )
            for _, r in df_colab.iterrows()
        }
        colab_sel = st.selectbox(
            "Selecione o Colaborador", options=list(colab_dict.keys())
        )
        dt_realizacao = st.date_input(
            "Data de Aplicação", dt_module.date.today()
        )
      with c2:
        treino_dict = {
            f"{r['nome_curso']} ({r['carga_horaria']}h)": (
                r["id"],
                r["frequencia"],
                r.get("custo_estimado") or 0.0,
                r["nome_curso"],
                r["carga_horaria"],
                r.get("aplicador_padrao"),
                r.get("aplicador_cargo_padrao"),
            )
            for _, r in df_treino.iterrows()
        }
        treino_sel = st.selectbox(
            "Selecione o Treinamento", options=list(treino_dict.keys())
        )
        validade = st.number_input(
            "Validade da Reciclagem (em meses)",
            min_value=1,
            max_value=60,
            value=12,
        )

      _, _, _, _, _, ap_padrao_txt, ap_cargo_padrao_txt = treino_dict[
          treino_sel
      ]

      c_a1, c_a2 = st.columns(2)
      with c_a1:
        aplicador_input_nome = st.text_input(
            "Nome do Aplicador", value=ap_padrao_txt or "Aplicador Técnico"
        )
      with c_a2:
        aplicador_input_cargo = st.text_input(
            "Cargo do Aplicador",
            value=ap_cargo_padrao_txt or "Aplicador do Treinamento",
        )

      c_v1, c_v2 = st.columns(2)
      with c_v1:
        custo_input = st.number_input(
            "Custo da Capacitação (R$)",
            min_value=0.0,
            value=float(treino_dict[treino_sel][2] or 0.0),
        )
      with c_v2:
        uploaded_file = st.file_uploader(
            "📎 Anexar Evidência Manual (Forms/Lista de Presença)",
            type=["pdf", "png", "jpg", "jpeg"],
        )

      if st.form_submit_button("✅ Gravar Registro e Gerar Evidência"):
        cid, c_nome_txt, c_cargo_txt = colab_dict[colab_sel]
        tid, t_freq, t_custo, t_nome_txt, t_horas_val, _, _ = treino_dict[
            treino_sel
        ]

        nome_cert_auto = f"Certificado_AUTO_{cid}_{tid}_{dt_realizacao}.pdf"
        pdf_bytes_cert = gerar_pdf_certificado(
            colab_nome=c_nome_txt,
            colab_cargo=c_cargo_txt,
            curso_nome=t_nome_txt,
            carga_horaria=t_horas_val,
            data_realizacao=dt_realizacao,
            aplicador_nome=aplicador_input_nome,
            aplicador_cargo=aplicador_input_cargo,
        )
        salvar_arquivo_supabase(nome_cert_auto, pdf_bytes_cert.getvalue())

        nome_forms_val = "Sem anexo"
        if uploaded_file is not None:
          nome_forms_val = (
              f"Forms_{cid}_{tid}_{dt_realizacao}_{uploaded_file.name}"
          )
          salvar_arquivo_supabase(
              nome_forms_val,
              uploaded_file.getvalue(),
              content_type=uploaded_file.type,
          )

        payload = {
            "colaborador_id": cid,
            "treinamento_id": tid,
            "data_realizacao": dt_realizacao.strftime("%Y-%m-%d"),
            "validade_meses": validade,
            "status_planilha": "Concluído",
            "arquivo_evidencia": nome_cert_auto,
            "arquivo_forms": nome_forms_val,
            "instrutor_nome": aplicador_input_nome,
            "aplicador_cargo": aplicador_input_cargo,
            "custo_real": custo_input,
        }

        check_db = (
            supabase.table("registros")
            .select("id")
            .eq("colaborador_id", cid)
            .eq("treinamento_id", tid)
            .execute()
        )
        if check_db.data:
          supabase.table("registros").update(payload).eq(
              "id", check_db.data[0]["id"]
          ).execute()
        else:
          supabase.table("registros").insert(payload).execute()

        registrar_log(
            st.session_state["nome_usuario"],
            "LANÇAMENTO DE TREINAMENTO",
            f"Treino ID {tid} para Colab ID {cid}",
        )
        st.success(
            "🎉 Treinamento gravado e Certificado"
            f" `{nome_cert_auto}` gerado com sucesso!"
        )

# -------------------------------------------------------------------
# 4. CATÁLOGO DE TREINAMENTOS
# -------------------------------------------------------------------
elif pagina == "📚 Catálogo de Treinamentos":
  st.markdown(
      '<div class="main-header">📚 Catálogo de Treinamentos, Normas e'
      " Aplicadores Padrão</div>",
      unsafe_allow_html=True,
  )

  t_cat_list, t_cat_add, t_cat_edit = st.tabs([
      "📋 Listagem Completa",
      "➕ Incluir Novo Treinamento",
      "✏️ Editar Cadastro / Aplicador Padrão",
  ])

  with t_cat_list:
    res_t = (
        supabase.table("treinamentos")
        .select("*")
        .order("nome_curso")
        .execute()
    )
    df_t = pd.DataFrame(res_t.data)
    st.dataframe(df_t, use_container_width=True)

  with t_cat_add:
    with st.form("form_add_treino"):
      st.subheader("➕ Novo Treinamento no Catálogo")
      n_curso = st.text_input(
          "Nome do Treinamento / Norma (ex: NR-10 Segurança em Elétrica)"
      )
      c_t1, c_t2, c_t3 = st.columns(3)
      with c_t1:
        n_ch = st.number_input(
            "Carga Horária (horas)", min_value=0.5, value=1.0, step=0.5
        )
      with c_t2:
        n_freq = st.selectbox(
            "Frequência / Validade",
            [
                "Anual",
                "Bienal (2 anos)",
                "Trienal (3 anos)",
                "Eventual / Admissional",
            ],
        )
      with c_t3:
        n_classif = st.selectbox(
            "Classificação",
            [
                "Obrigatório (NR)",
                "Processo / Qualidade (ISO)",
                "Integração",
                "Opcional",
            ],
        )

      c_a1, c_a2 = st.columns(2)
      with c_a1:
        n_ap_nome = st.text_input(
            "Nome do Aplicador Padrão", "Aplicador Técnico"
        )
      with c_a2:
        n_ap_cargo = st.text_input(
            "Cargo do Aplicador Padrão", "Aplicador do Treinamento"
        )

      if st.form_submit_button("➕ Salvar Treinamento"):
        if n_curso.strip():
          supabase.table("treinamentos").insert({
              "nome_curso": n_curso.strip(),
              "carga_horaria": n_ch,
              "frequencia": n_freq,
              "classificacao": n_classif,
              "aplicador_padrao": n_ap_nome.strip(),
              "aplicador_cargo_padrao": n_ap_cargo.strip(),
          }).execute()
          registrar_log(
              st.session_state["nome_usuario"],
              "INCLUSÃO TREINAMENTO",
              f"Incluído curso: {n_curso}",
          )
          st.success(f"Treinamento '{n_curso}' adicionado com sucesso!")
          st.rerun()

  with t_cat_edit:
    res_t_edit = (
        supabase.table("treinamentos")
        .select("*")
        .order("nome_curso")
        .execute()
    )
    df_t_edit = pd.DataFrame(res_t_edit.data)
    if not df_t_edit.empty:
      curso_sel_e = st.selectbox(
          "Selecione o Treinamento para Editar:",
          df_t_edit["nome_curso"].tolist(),
      )
      row_e = df_t_edit[df_t_edit["nome_curso"] == curso_sel_e].iloc[0]

      with st.form("form_edit_treino"):
        st.subheader(f"✏️ Editar: {row_e['nome_curso']}")
        e_curso = st.text_input(
            "Nome do Treinamento / Norma", value=row_e["nome_curso"]
        )
        e_c1, e_c2, e_c3 = st.columns(3)
        with e_c1:
          e_ch = st.number_input(
              "Carga Horária (horas)",
              min_value=0.5,
              value=float(row_e["carga_horaria"]),
              step=0.5,
          )
        with e_c2:
          e_freq = st.selectbox(
              "Frequência / Validade",
              [
                  "Anual",
                  "Bienal (2 anos)",
                  "Trienal (3 anos)",
                  "Eventual / Admissional",
              ],
              index=0,
          )
        with e_c3:
          e_classif = st.selectbox(
              "Classificação",
              [
                  "Obrigatório (NR)",
                  "Processo / Qualidade (ISO)",
                  "Integração",
                  "Opcional",
              ],
              index=0,
          )

        e_a1, e_a2 = st.columns(2)
        with e_a1:
          e_ap_nome = st.text_input(
              "Nome do Aplicador Padrão",
              value=row_e.get("aplicador_padrao") or "Aplicador Técnico",
          )
        with e_a2:
          e_ap_cargo = st.text_input(
              "Cargo do Aplicador Padrão",
              value=row_e.get("aplicador_cargo_padrao")
              or "Aplicador do Treinamento",
          )

        if st.form_submit_button("💾 Salvar Alterações no Catálogo"):
          supabase.table("treinamentos").update({
              "nome_curso": e_curso.strip(),
              "carga_horaria": e_ch,
              "frequencia": e_freq,
              "classificacao": e_classif,
              "aplicador_padrao": e_ap_nome.strip(),
              "aplicador_cargo_padrao": e_ap_cargo.strip(),
          }).eq("id", int(row_e["id"])).execute()
          registrar_log(
              st.session_state["nome_usuario"],
              "EDIÇÃO TREINAMENTO",
              f"Atualizado curso ID {row_e['id']}: {e_curso}",
          )
          st.success("Cadastro do treinamento atualizado no catálogo!")
          st.rerun()

# -------------------------------------------------------------------
# 5. CERTIFICADOS & PRESENÇA
# -------------------------------------------------------------------
elif pagina == "📜 Certificados & Presença":
  st.markdown(
      '<div class="main-header">📜 Emissão de Certificados e Listas de Presença'
      f" ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )
  t_cert, t_lista = st.tabs([
      "📜 Emitir Certificado Individual",
      "📝 Gerar Lista de Presença para Treinamento",
  ])

  with t_cert:
    st.subheader(
        "📜 Gerador de Certificado em PDF com Logo e 3 Assinaturas"
    )
    res_regs = (
        supabase.table("registros")
        .select(
            "data_realizacao, instrutor_nome, aplicador_cargo,"
            " colaboradores(nome, cargo), treinamentos(nome_curso,"
            " carga_horaria)"
        )
        .execute()
    )

    flat_regs = []
    if res_regs.data:
      for r in res_regs.data:
        dt_r = r.get("data_realizacao")
        if dt_r and str(dt_r).startswith(str(ano_exercicio)):
          c = r.get("colaboradores") or {}
          t = r.get("treinamentos") or {}
          flat_regs.append({
              "Colaborador": c.get("nome"),
              "Cargo": c.get("cargo"),
              "Treinamento": t.get("nome_curso"),
              "Horas": t.get("carga_horaria"),
              "Data": dt_r,
              "Instrutor": r.get("instrutor_nome"),
              "AplicadorCargo": r.get("aplicador_cargo"),
          })

    df_regs = pd.DataFrame(flat_regs)

    if df_regs.empty:
      st.info(
          "Nenhum treinamento registrado em"
          f" {ano_exercicio} para emissão de certificado."
      )
    else:
      opt_cert = [
          f"{r['Colaborador']} — {r['Treinamento']} ({r['Data']})"
          for _, r in df_regs.iterrows()
      ]
      sel_cert = st.selectbox(
          "Selecione a Capacitação Realizada:", opt_cert
      )
      idx_sel = opt_cert.index(sel_cert)
      row_cert = df_regs.iloc[idx_sel]

      pdf_cert_bytes = gerar_pdf_certificado(
          colab_nome=row_cert["Colaborador"],
          colab_cargo=row_cert["Cargo"],
          curso_nome=row_cert["Treinamento"],
          carga_horaria=row_cert["Horas"],
          data_realizacao=row_cert["Data"],
          aplicador_nome=row_cert["Instrutor"] or "Aplicador Técnico",
          aplicador_cargo=row_cert["AplicadorCargo"]
          or "Aplicador do Treinamento",
      )
      st.download_button(
          label=(
              "🎓 Baixar Certificado Oficial em PDF"
              f" ({row_cert['Colaborador']})"
          ),
          data=pdf_cert_bytes,
          file_name=(
              f"Certificado_{row_cert['Colaborador'].replace(' ', '_')}_{row_cert['Treinamento'][:15]}.pdf"
          ),
          mime="application/pdf",
          type="primary",
      )

  with t_lista:
    st.subheader(
        "📝 Gerador de Lista de Presença para Aplicação Presencial"
        f" ({ano_exercicio})"
    )
    res_t_l = (
        supabase.table("treinamentos")
        .select("id, nome_curso, carga_horaria")
        .order("nome_curso")
        .execute()
    )
    df_treinos_l = pd.DataFrame(res_t_l.data)
    deptos_l = get_lista_departamentos()

    c_l1, c_l2 = st.columns(2)
    with c_l1:
      treino_l_sel = st.selectbox(
          "Selecione o Treinamento:", df_treinos_l["nome_curso"].tolist()
      )
    with c_l2:
      depto_l_sel = st.selectbox(
          "Filtrar Colaboradores do Setor:",
          ["TODOS OS SETORES"] + deptos_l,
      )

    row_t_info = df_treinos_l[
        df_treinos_l["nome_curso"] == treino_l_sel
    ].iloc[0]

    if depto_l_sel == "TODOS OS SETORES":
      res_cl = (
          supabase.table("colaboradores")
          .select("nome, cargo")
          .order("nome")
          .execute()
      )
    else:
      res_cl = (
          supabase.table("colaboradores")
          .select("nome, cargo")
          .eq("departamento", depto_l_sel)
          .order("nome")
          .execute()
      )

    df_colabs_lista = pd.DataFrame(res_cl.data)

    st.write(
        f"**Total de participantes na lista:** `{len(df_colabs_lista)}`"
        " colaboradores."
    )
    if not df_colabs_lista.empty:
      lista_dict = df_colabs_lista.to_dict("records")
      pdf_lista_bytes = gerar_pdf_lista_presenca(
          row_t_info["nome_curso"],
          row_t_info["carga_horaria"],
          depto_l_sel,
          lista_dict,
          ano_exercicio,
      )
      st.download_button(
          label=(
              "🖨️ Imprimir Lista de Presença em PDF (Para Assinatura Física)"
          ),
          data=pdf_lista_bytes,
          file_name=(
              f"Lista_Presenca_{treino_l_sel[:15]}_{ano_exercicio}.pdf"
          ),
          mime="application/pdf",
      )

# -------------------------------------------------------------------
# 6. EVOLUÇÃO POR TREINAMENTO
# -------------------------------------------------------------------
elif pagina == "📈 Evolução por Treinamento":
  st.markdown(
      '<div class="main-header">📈 Evolução Geral por Treinamento'
      f" ({ano_exercicio}): Previstos vs. Realizados</div>",
      unsafe_allow_html=True,
  )
  res_colabs_count = (
      supabase.table("colaboradores").select("id", count="exact").execute()
  )
  total_colabs = res_colabs_count.count or 0

  res_t = supabase.table("treinamentos").select("*").execute()
  res_r = supabase.table("registros").select("treinamento_id, data_realizacao, status_planilha").execute()

  df_t = pd.DataFrame(res_t.data)
  df_r = pd.DataFrame(res_r.data)

  if df_t.empty:
    st.info("Nenhum treinamento cadastrado.")
  else:
    if not df_r.empty:
      df_r_ano = df_r[
          (df_r["status_planilha"] == "Concluído")
          & (df_r["data_realizacao"].astype(str).str.startswith(str(ano_exercicio)))
      ]
      counts = df_r_ano["treinamento_id"].value_counts().to_dict()
    else:
      counts = {}

    df_t["Realizados"] = df_t["id"].map(lambda x: counts.get(x, 0))
    df_t["Previstos"] = total_colabs
    df_t["Atingimento (%)"] = (
        (df_t["Realizados"] / df_t["Previstos"]) * 100
    ).round(1)
    df_t["Horas Acumuladas"] = df_t["Realizados"] * df_t["carga_horaria"]

    filtro_curso = st.text_input("🔍 Buscar Treinamento/Norma:", "")
    if filtro_curso:
      df_t = df_t[
          df_t["nome_curso"].str.contains(filtro_curso, case=False, na=False)
      ]

    fig_comp = px.bar(
        df_t,
        x="nome_curso",
        y=["Realizados", "Previstos"],
        barmode="group",
        labels={"value": "Pessoas", "variable": "Status"},
        color_discrete_map={"Realizados": "#10B981", "Previstos": "#64748B"},
    )
    fig_comp.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_comp, use_container_width=True)
    st.divider()
    st.dataframe(
        df_t[[
            "nome_curso",
            "classificacao",
            "carga_horaria",
            "Previstos",
            "Realizados",
            "Atingimento (%)",
            "Horas Acumuladas",
        ]],
        use_container_width=True,
    )

# -------------------------------------------------------------------
# 7. GESTÃO DE COLABORADORES
# -------------------------------------------------------------------
elif pagina == "👥 Gestão de Colaboradores":
  st.markdown(
      '<div class="main-header">👥 Gestão de Colaboradores</div>',
      unsafe_allow_html=True,
  )
  t_list, t_add, t_edit, t_del = st.tabs([
      "📋 Listagem",
      "➕ Incluir Novo",
      "✏️ Editar Cadastro",
      "❌ Excluir Colaborador",
  ])
  deptos_existentes = get_lista_departamentos()

  with t_list:
    res_c = (
        supabase.table("colaboradores")
        .select("id, nome, cargo, gestor, departamento, genero, email")
        .order("nome")
        .execute()
    )
    df_c = pd.DataFrame(res_c.data)
    st.dataframe(df_c, use_container_width=True)

  with t_add:
    with st.form("form_add_colab"):
      st.subheader("➕ Novo Colaborador")
      n_nome = st.text_input("Nome Completo")
      n_cargo = st.text_input("Cargo / Função")
      n_gestor = st.text_input("Gestor Direto")
      n_email = st.text_input("E-mail Corporativo")
      c_s1, c_s2 = st.columns(2)
      with c_s1:
        depto_sel_list = st.selectbox(
            "Selecionar Setor Existente:",
            options=["-- Selecionar ou Criar Novo --"] + deptos_existentes,
        )
      with c_s2:
        depto_novo_text = st.text_input(
            "OU Digite um Novo Setor / Departamento:"
        )
      n_genero = st.selectbox("Gênero", ["Masculino", "Feminino"])

      if st.form_submit_button("➕ Salvar Novo Colaborador"):
        setor_final = (
            depto_novo_text.strip().upper()
            if depto_novo_text.strip()
            else (
                depto_sel_list
                if depto_sel_list != "-- Selecionar ou Criar Novo --"
                else ""
            )
        )
        if n_nome.strip() and setor_final:
          try:
            supabase.table("colaboradores").insert({
                "nome": n_nome.strip(),
                "departamento": setor_final,
                "cargo": n_cargo.strip(),
                "gestor": n_gestor.strip(),
                "genero": n_genero,
                "email": n_email.strip(),
            }).execute()
            registrar_log(
                st.session_state["nome_usuario"],
                "INCLUSÃO COLABORADOR",
                f"Incluído: {n_nome} ({setor_final})",
            )
            st.success(
                f"Colaborador '{n_nome}' incluído no setor '{setor_final}'"
                " com sucesso!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Erro: {e}")

  with t_edit:
    res_c_edit = (
        supabase.table("colaboradores").select("*").order("nome").execute()
    )
    df_c_edit = pd.DataFrame(res_c_edit.data)
    if not df_c_edit.empty:
      colab_sel_edit = st.selectbox(
          "Selecione o Colaborador para Editar:", df_c_edit["nome"].tolist()
      )
      row_edit = df_c_edit[df_c_edit["nome"] == colab_sel_edit].iloc[0]
      with st.form("form_edit_colab"):
        st.subheader(f"✏️ Editar Cadastro: {row_edit['nome']}")
        e_nome = st.text_input("Nome Completo", value=row_edit["nome"])
        e_cargo = st.text_input(
            "Cargo / Função", value=row_edit["cargo"] or ""
        )
        e_gestor = st.text_input(
            "Gestor Direto", value=row_edit["gestor"] or ""
        )
        e_email = st.text_input(
            "E-mail Corporativo", value=row_edit["email"] or ""
        )
        e_s1, e_s2 = st.columns(2)
        setor_atual = row_edit["departamento"]
        list_options = (
            deptos_existentes
            if setor_atual in deptos_existentes
            else [setor_atual] + deptos_existentes
        )
        idx_atual = (
            list_options.index(setor_atual) if setor_atual in list_options else 0
        )
        with e_s1:
          e_depto_sel = st.selectbox(
              "Selecionar da Lista Existente:",
              options=list_options,
              index=idx_atual,
          )
        with e_s2:
          e_depto_novo = st.text_input("OU Digite para Alterar o Setor:")
        e_genero = st.selectbox(
            "Gênero",
            ["Masculino", "Feminino"],
            index=0 if row_edit["genero"] == "Masculino" else 1,
        )

        if st.form_submit_button("💾 Salvar Alterações"):
          e_setor_final = (
              e_depto_novo.strip().upper()
              if e_depto_novo.strip()
              else e_depto_sel
          )
          supabase.table("colaboradores").update({
              "nome": e_nome.strip(),
              "departamento": e_setor_final,
              "cargo": e_cargo.strip(),
              "gestor": e_gestor.strip(),
              "genero": e_genero,
              "email": e_email.strip(),
          }).eq("id", int(row_edit["id"])).execute()
          registrar_log(
              st.session_state["nome_usuario"],
              "EDIÇÃO COLABORADOR",
              f"Editado ID {row_edit['id']}: '{e_nome}'",
          )
          st.success("Cadastro atualizado com sucesso!")
          st.rerun()

  with t_del:
    res_c_del = (
        supabase.table("colaboradores")
        .select("id, nome, departamento")
        .order("nome")
        .execute()
    )
    df_c_del = pd.DataFrame(res_c_del.data)
    if not df_c_del.empty:
      colab_sel_del = st.selectbox(
          "Selecione o Colaborador para Excluir:", df_c_del["nome"].tolist()
      )
      row_del = df_c_del[df_c_del["nome"] == colab_sel_del].iloc[0]
      st.warning(
          f"⚠️ Atenção: A exclusão do colaborador **{row_del['nome']}** apagará"
          " todo o seu histórico."
      )
      if st.button("🗑️ Confirmar Exclusão Permanente", type="primary"):
        supabase.table("colaboradores").delete().eq(
            "id", int(row_del["id"])
        ).execute()
        supabase.table("registros").delete().eq(
            "colaborador_id", int(row_del["id"])
        ).execute()
        registrar_log(
            st.session_state["nome_usuario"],
            "EXCLUSÃO COLABORADOR",
            f"Excluído colaborador ID {row_del['id']}: {row_del['nome']}",
        )
        st.success("Colaborador removido com sucesso!")
        st.rerun()

# -------------------------------------------------------------------
# 8. MATRIZ POR CARGO (LNT)
# -------------------------------------------------------------------
elif pagina == "🎯 Matriz por Cargo (LNT)":
  st.markdown(
      '<div class="main-header">🎯 Matriz de Treinamentos Obrigatórios por Cargo'
      " (LNT)</div>",
      unsafe_allow_html=True,
  )
  res_cargos = (
      supabase.table("colaboradores").select("cargo").neq("cargo", "").execute()
  )
  df_cargos = pd.DataFrame(res_cargos.data)
  if not df_cargos.empty:
    cargos_lista = sorted(df_cargos["cargo"].unique().tolist())
    cargo_sel = st.selectbox(
        "Selecione o Cargo para Configurar:", cargos_lista
    )

    res_t_todos = (
        supabase.table("treinamentos")
        .select("id, nome_curso, classificacao")
        .order("nome_curso")
        .execute()
    )
    df_treinos_todos = pd.DataFrame(res_t_todos.data)

    res_m = (
        supabase.table("matriz_cargo_treinamento")
        .select("treinamento_id")
        .eq("cargo", cargo_sel)
        .execute()
    )
    atuais_ids = [r["treinamento_id"] for r in res_m.data] if res_m.data else []

    with st.form("form_matriz_lnt"):
      st.write(
          "**Selecione os treinamentos OBRIGATÓRIOS para a função"
          f" `{cargo_sel}`:**"
      )
      novos_selecionados = []
      for _, r_t in df_treinos_todos.iterrows():
        marcado = r_t["id"] in atuais_ids
        if st.checkbox(
            f"{r_t['nome_curso']} ({r_t['classificacao']})",
            value=marcado,
            key=f"chk_{r_t['id']}",
        ):
          novos_selecionados.append(r_t["id"])
      if st.form_submit_button("💾 Salvar Matriz do Cargo"):
        supabase.table("matriz_cargo_treinamento").delete().eq(
            "cargo", cargo_sel
        ).execute()
        for tid in novos_selecionados:
          supabase.table("matriz_cargo_treinamento").insert(
              {"cargo": cargo_sel, "treinamento_id": tid}
          ).execute()
        registrar_log(
            st.session_state["nome_usuario"],
            "ATUALIZAÇÃO LNT",
            f"Atualizada matriz para o cargo {cargo_sel}",
        )
        st.success(f"Matriz LNT para `{cargo_sel}` salva com sucesso!")

# -------------------------------------------------------------------
# 9. GESTÃO DE USUÁRIOS
# -------------------------------------------------------------------
elif pagina == "🔑 Gestão de Usuários":
  st.markdown(
      '<div class="main-header">🔑 Gestão de Usuários e Perfis</div>',
      unsafe_allow_html=True,
  )
  res_u = (
      supabase.table("usuarios")
      .select("id, login, nome, perfil")
      .order("login")
      .execute()
  )
  df_users = pd.DataFrame(res_u.data)
  st.dataframe(df_users, use_container_width=True)

# -------------------------------------------------------------------
# 10. GESTÃO ORÇAMENTÁRIA
# -------------------------------------------------------------------
elif pagina == "💰 Gestão Orçamentária":
  st.markdown(
      '<div class="main-header">💰 Gestão Financeira de Capacitação'
      f" ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )
  res_c = (
      supabase.table("registros")
      .select(
          "custo_real, data_realizacao, colaboradores(departamento),"
          " treinamentos(nome_curso)"
      )
      .execute()
  )
  flat_cost = []
  if res_c.data:
    for r in res_c.data:
      dt_r = r.get("data_realizacao")
      if dt_r and str(dt_r).startswith(str(ano_exercicio)):
        c = r.get("colaboradores") or {}
        t = r.get("treinamentos") or {}
        flat_cost.append({
            "Departamento": c.get("departamento"),
            "Treinamento": t.get("nome_curso"),
            "CustoReal": float(r.get("custo_real") or 0.0),
        })

  df_cost = pd.DataFrame(flat_cost)
  if not df_cost.empty:
    st.metric(
        "💰 Investimento Total Cumprido no Ano",
        f"R$ {df_cost['CustoReal'].sum():,.2f}",
    )
    st.dataframe(df_cost, use_container_width=True)
  else:
    st.info(f"Nenhum custo registrado para {ano_exercicio}.")

# -------------------------------------------------------------------
# 11. RELATÓRIOS P/ AUDITORIA
# -------------------------------------------------------------------
elif pagina == "📂 Relatórios p/ Auditoria":
  st.markdown(
      '<div class="main-header">📂 Exportação Oficial de Relatórios'
      f" ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )
  res_rep = (
      supabase.table("registros")
      .select(
          "data_realizacao, arquivo_evidencia, colaboradores(nome, cargo,"
          " departamento), treinamentos(nome_curso, carga_horaria)"
      )
      .execute()
  )
  flat_rep = []
  if res_rep.data:
    for r in res_rep.data:
      dt_r = r.get("data_realizacao")
      if dt_r and str(dt_r).startswith(str(ano_exercicio)):
        c = r.get("colaboradores") or {}
        t = r.get("treinamentos") or {}
        flat_rep.append({
            "Nome Colaborador": c.get("nome"),
            "Cargo": c.get("cargo"),
            "Departamento": c.get("departamento"),
            "Treinamento": t.get("nome_curso"),
            "Horas": t.get("carga_horaria"),
            "Data Realização": dt_r,
            "Evidência": r.get("arquivo_evidencia"),
        })

  df_report = pd.DataFrame(flat_rep)
  if not df_report.empty:
    st.dataframe(df_report, use_container_width=True)
    st.download_button(
        "📥 Baixar Relatório (CSV)",
        df_report.to_csv(index=False).encode("utf-8"),
        f"Relatorio_MAQ_{ano_exercicio}.csv",
        "text/csv",
    )
  else:
    st.info(f"Nenhum relatório encontrado para o ano de {ano_exercicio}.")

# -------------------------------------------------------------------
# 12. LOGS DE AUDITORIA
# -------------------------------------------------------------------
elif pagina == "📜 Logs de Auditoria":
  st.markdown(
      '<div class="main-header">📜 Trilha de Auditoria (Audit Trail)</div>',
      unsafe_allow_html=True,
  )
  res_logs = (
      supabase.table("logs_auditoria")
      .select("timestamp, usuario, acao, detalhes")
      .order("id", desc=True)
      .execute()
  )
  df_logs = pd.DataFrame(res_logs.data)
  st.dataframe(df_logs, use_container_width=True)
