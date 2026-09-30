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


# Funções utilitárias de limpeza de dados
def limpar_valor(val):
  if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", ""]:
    return None
  return str(val).strip()


# -------------------------------------------------------------------
# CONEXÃO COM O SUPABASE
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
# AUTENTICAÇÃO E PERFIS
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
    st.caption(
        "🔒 Acesso Restrito ao Sistema de Compliance e Treinamentos (Supabase"
        " Cloud)"
    )

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
                u["nome"], "LOGIN", f"Usuário {u['login']} efetuou login."
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
# MENU LATERAL
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
    if st.button(opt, use_container_width=True):
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
# PÁGINAS DO SISTEMA
# -------------------------------------------------------------------
if pagina == "📊 Dashboard Executivo":
  st.markdown(
      '<div class="main-header">📊 Dashboard Geral de Performance e Compliance'
      f" Executivo ({ano_exercicio})</div>",
      unsafe_allow_html=True,
  )

  res_reg = (
      supabase.table("registros")
      .select(
          "data_realizacao, validade_meses, colaboradores(nome, departamento),"
          " treinamentos(nome_curso, carga_horaria, classificacao)"
      )
      .execute()
  )

  if not res_reg.data:
    st.info(
        "💡 Nenhum registro cadastrado no banco de dados para o ano de"
        f" {ano_exercicio}."
    )
  else:
    flat_data = []
    for r in res_reg.data:
      dt_r = r.get("data_realizacao")
      if dt_r and str(dt_r).startswith(str(ano_exercicio)):
        flat_data.append({
            "Colaborador": r["colaboradores"]["nome"],
            "Departamento": r["colaboradores"]["departamento"],
            "Treinamento": r["treinamentos"]["nome_curso"],
            "Horas": float(r["treinamentos"]["carga_horaria"] or 0),
            "Classificacao": r["treinamentos"]["classificacao"],
            "DataRealizacao": dt_r,
            "ValidadeMeses": int(r["validade_meses"] or 12),
        })

    df = pd.DataFrame(flat_data)
    res_colabs_count = (
        supabase.table("colaboradores").select("id", count="exact").execute()
    )
    df_colabs_total = res_colabs_count.count or 0

    if df.empty:
      st.info(
          f"💡 Nenhum registro encontrado para o exercício {ano_exercicio}."
      )
    else:
      df["DataRealizacao"] = pd.to_datetime(df["DataRealizacao"])
      df["DataVencimento"] = df.apply(
          lambda row: row["DataRealizacao"]
          + pd.DateOffset(months=row["ValidadeMeses"]),
          axis=1,
      )
      hoje = pd.to_datetime(dt_module.date.today())
      df["DiasParaVencer"] = (df["DataVencimento"] - hoj).dt.days

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
      k2.metric("⏱️ Horas Capacitadas", f"{total_horas:.1f}h")
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

    # Consulta direta dos registros atuais do colaborador
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
            "Treinamento": r["treinamentos"]["nome_curso"],
            "Classificacao": r["treinamentos"]["classificacao"],
            "Horas": float(r["treinamentos"]["carga_horaria"] or 0),
            "DataRealizacao": r.get("data_realizacao"),
            "ValidadeMeses": int(r.get("validade_meses") or 12),
            "Evidencia": r.get("arquivo_evidencia"),
            "Forms": r.get("arquivo_forms"),
            "Instrutor": r.get("instrutor_nome"),
            "AplicadorCargo": r.get("aplicador_cargo"),
        })
    df_realizados = pd.DataFrame(flat_ind)

    st.markdown(
        f"""
        <div class="colab-card">
            <h3 style="margin-top:0;">👤 <b>{colab_info['nome']}</b></h3>
            <p style="margin-bottom:5px;">💼 <b>Cargo:</b> {colab_info['cargo'] or 'N/A'} &nbsp;|&nbsp; 👔 <b>Gestor:</b> {colab_info['gestor'] or 'N/A'}</p>
            <p style="margin-bottom:0;">🏢 <b>Departamento:</b> {colab_info['departamento']} &nbsp;|&nbsp; ✉️ <b>E-mail:</b> {colab_info['email'] or 'N/A'}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("📋 Gestão Individual por Treinamento (Supabase Cloud Sync)")
    ids_realizados = (
        df_realizados["TreinamentoID"].tolist()
        if not df_realizados.empty
        else []
    )

    for _, r_t in df_lnt_cargo.iterrows():
      tid = int(r_t["id"])
      nome_curso = r_t["nome_curso"]
      ch_val = r_t["carga_horaria"]

      is_concluido = tid in ids_realizados
      reg_info = (
          df_realizados[df_realizados["TreinamentoID"] == tid].iloc[0]
          if is_concluido
          else None
      )

      with st.container():
        st.markdown(
            f"#### 📚 {nome_curso} ({ch_val}h - {r_t['classificacao']})"
        )
        col_c1, col_c2, col_c3, col_c4, col_c5, col_c6 = st.columns(
            [2, 2, 2, 2, 2.5, 2]
        )

        with col_c1:
          novo_status = st.selectbox(
              "Status",
              ["🔴 Pendente", "🟢 Concluído"],
              index=1 if is_concluido else 0,
              key=f"status_{cid}_{tid}",
          )
        with col_c2:
          dt_def = (
              pd.to_datetime(reg_info["DataRealizacao"]).date()
              if is_concluido and reg_info["DataRealizacao"]
              else dt_module.date.today()
          )
          nova_data = st.date_input(
              "Data Aplicação", value=dt_def, key=f"data_{cid}_{tid}"
          )
        with col_c3:
          inst_def = (
              reg_info["Instrutor"]
              if (is_concluido and reg_info["Instrutor"])
              else (r_t.get("aplicador_padrao") or "Aplicador Técnico")
          )
          nome_aplicador = st.text_input(
              "Nome Aplicador",
              value=limpar_valor(inst_def) or "",
              key=f"inst_{cid}_{tid}",
          )
        with col_c4:
          cargo_def = (
              reg_info["AplicadorCargo"]
              if (is_concluido and reg_info.get("AplicadorCargo"))
              else (
                  r_t.get("aplicador_cargo_padrao")
                  or "Aplicador do Treinamento"
              )
          )
          cargo_aplicador = st.text_input(
              "Cargo Aplicador",
              value=limpar_valor(cargo_def) or "",
              key=f"acargo_{cid}_{tid}",
          )
        with col_c5:
          up_f = st.file_uploader(
              "📎 Anexar Forms/Lista",
              type=["pdf", "png", "jpg"],
              key=f"up_{cid}_{tid}",
          )
        with col_c6:
          st.write("📄 **Ações / Download:**")
          if is_concluido and reg_info is not None:
            cert_file = reg_info["Evidencia"]
            if cert_file:
              b_cert = baixar_arquivo_supabase(cert_file)
              if b_cert:
                st.download_button(
                    "🎓 Baixar Certificado",
                    b_cert,
                    file_name=cert_file,
                    key=f"dl_c_{cid}_{tid}",
                )

            forms_file = reg_info["Forms"]
            if forms_file and str(forms_file).strip().lower() not in [
                "sem anexo",
                "none",
                "nan",
                "",
            ]:
              b_forms = baixar_arquivo_supabase(forms_file)
              if b_forms:
                st.download_button(
                    "📎 Baixar Forms/Lista",
                    b_forms,
                    file_name=forms_file,
                    key=f"dl_f_{cid}_{tid}",
                )

        # SALVAMENTO COMPLETO E LIMPEZA DE CACHE
        if st.button(
            f"💾 Salvar Atualização de '{nome_curso}'",
            key=f"btn_save_{cid}_{tid}",
        ):
          dt_str = nova_data.strftime("%Y-%m-%d")

          try:
            if novo_status == "🟢 Concluído":
              nome_forms_salvo = (
                  reg_info["Forms"] if is_concluido else "Sem anexo"
              )
              if up_f is not None:
                nome_forms_salvo = f"Forms_{cid}_{tid}_{dt_str}_{up_f.name}"
                salvar_arquivo_supabase(
                    nome_forms_salvo,
                    up_f.getvalue(),
                    content_type=up_f.type,
                )

              # 1. Gera o PDF do Certificado
              nome_cert_auto = f"Certificado_AUTO_{cid}_{tid}_{dt_str}.pdf"
              pdf_bytes_cert = gerar_pdf_certificado(
                  colab_nome=str(colab_info["nome"]),
                  colab_cargo=str(colab_info["cargo"] or ""),
                  curso_nome=str(nome_curso),
                  carga_horaria=str(ch_val),
                  data_realizacao=dt_str,
                  aplicador_nome=limpar_valor(nome_aplicador)
                  or "Aplicador Técnico",
                  aplicador_cargo=limpar_valor(cargo_aplicador)
                  or "Aplicador do Treinamento",
              )

              # 2. Upload do PDF para o Storage
              salvar_arquivo_supabase(
                  nome_cert_auto, pdf_bytes_cert.getvalue()
              )

              payload = {
                  "colaborador_id": cid,
                  "treinamento_id": tid,
                  "data_realizacao": dt_str,
                  "validade_meses": 12,
                  "status_planilha": "Concluído",
                  "arquivo_evidencia": nome_cert_auto,
                  "arquivo_forms": nome_forms_salvo,
                  "instrutor_nome": limpar_valor(nome_aplicador),
                  "aplicador_cargo": limpar_valor(cargo_aplicador),
                  "custo_real": 0.0,
              }

              # 3. Garante atualização do registro ou insere um novo
              check_db = (
                  supabase.table("registros")
                  .select("id")
                  .eq("colaborador_id", cid)
                  .eq("treinamento_id", tid)
                  .execute()
              )

              if check_db.data:
                reg_id_existente = check_db.data[0]["id"]
                supabase.table("registros").update(payload).eq(
                    "id", reg_id_existente
                ).execute()
              else:
                supabase.table("registros").insert(payload).execute()

              st.cache_data.clear()
              st.success(f"🎉 Certificado gerado para '{nome_curso}'!")
              st.rerun()

            elif novo_status == "🔴 Pendente" and is_concluido:
              # Remove do Storage
              if reg_info is not None:
                if reg_info.get("Evidencia"):
                  deletar_arquivo_supabase(reg_info["Evidencia"])
                if reg_info.get("Forms"):
                  deletar_arquivo_supabase(reg_info["Forms"])

              # Remove do Banco de Dados
              supabase.table("registros").delete().eq(
                  "colaborador_id", cid
              ).eq("treinamento_id", tid).execute()

              st.cache_data.clear()
              st.warning(f"🗑️ Registro e certificado de '{nome_curso}' removidos!")
              st.rerun()

          except Exception as err:
            st.error(f"Erro na gravação do registro: {err}")

        st.divider()

elif pagina == "📚 Catálogo de Treinamentos":
  st.markdown(
      '<div class="main-header">📚 Catálogo de Treinamentos, Normas e'
      " Aplicadores Padrão</div>",
      unsafe_allow_html=True,
  )

  t_cat_list, t_cat_add = st.tabs(
      ["📋 Listagem Completa", "➕ Incluir Novo Treinamento"]
  )

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
      n_curso = st.text_input("Nome do Treinamento / Norma")
      c_t1, c_t2, c_t3 = st.columns(3)
      with c_t1:
        n_ch = st.number_input(
            "Carga Horária (h)", min_value=0.5, value=1.0, step=0.5
        )
      with c_t2:
        n_freq = st.selectbox(
            "Validade",
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
            "Nome Aplicador Padrão", "Aplicador Técnico"
        )
      with c_a2:
        n_ap_cargo = st.text_input(
            "Cargo Aplicador Padrão", "Aplicador do Treinamento"
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
          st.cache_data.clear()
          st.success(
              f"Treinamento '{n_curso}' cadastrado no Supabase!"
          )
          st.rerun()

elif pagina == "👥 Gestão de Colaboradores":
  st.markdown(
      '<div class="main-header">👥 Gestão de Colaboradores</div>',
      unsafe_allow_html=True,
  )
  res_c = supabase.table("colaboradores").select("*").order("nome").execute()
  df_c = pd.DataFrame(res_c.data)
  st.dataframe(df_c, use_container_width=True)

elif pagina == "📜 Logs de Auditoria":
  st.markdown(
      '<div class="main-header">📜 Trilha de Auditoria (Audit Trail)</div>',
      unsafe_allow_html=True,
  )
  res_logs = (
      supabase.table("logs_auditoria")
      .select("*")
      .order("id", desc=True)
      .execute()
  )
  df_logs = pd.DataFrame(res_logs.data)
  st.dataframe(df_logs, use_container_width=True)
