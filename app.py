import streamlit as st
import pandas as pd
import datetime
import os
import io
import plotly.express as px
import psycopg2
from sqlalchemy import create_engine

# ReportLab para geração de PDFs oficiais
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, String

# Configuração da página corporativa
st.set_page_config(
    page_title="Sistema Enterprise de Gestão de Treinamentos - MAQ",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

UPLOADS_DIR = "evidencias"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Estilização CSS
st.markdown("""
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
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# CONEXÃO COM O SUPABASE (POSTGRESQL)
# -------------------------------------------------------------------
def get_db_uri():
    if "postgres" in st.secrets and "db_url" in st.secrets["postgres"]:
        return st.secrets["postgres"]["db_url"]
    return os.getenv("DATABASE_URL", "")

def get_db_connection():
    return psycopg2.connect(get_db_uri())

def get_db_engine():
    return create_engine(get_db_uri())

conn = get_db_connection()

def get_lista_departamentos():
    df_deptos = pd.read_sql_query("SELECT DISTINCT departamento FROM colaboradores WHERE departamento IS NOT NULL AND departamento != ''", get_db_engine())
    deptos = sorted(df_deptos['departamento'].tolist())
    if not deptos:
        deptos = ["EXECUÇÃO", "MANUTENÇÃO", "OPERAÇÃO", "ALMOXARIFE", "ADMINISTRATIVO", "SEGURANÇA (SSO)"]
    return deptos

def carregar_logo_empresa():
    nomes_possiveis = [
        "Logo_Attend_ Ambiental.png",
        "Logo_Attend_ Ambiental.jpg",
        "Logo_Attend_ Ambiental.jpeg",
        "Logo_Attend_Ambiental.png",
        "Logo_Attend_Ambiental.jpg",
        "logo.png"
    ]
    for nome in nomes_possiveis:
        if os.path.exists(nome):
            return nome
    return None

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

def registrar_log(usuario, acao, detalhes):
    with conn.cursor() as c:
        c.execute("INSERT INTO logs_auditoria (usuario, acao, detalhes) VALUES (%s, %s, %s)", (str(usuario), str(acao), str(detalhes)))
        conn.commit()

# TELA DE LOGIN
if st.session_state["usuario_logado"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c_center1, c_center2, c_center3 = st.columns([1, 2, 1])
    
    with c_center2:
        logo_caminho = carregar_logo_empresa()
        if logo_caminho:
            st.image(logo_caminho, width=220)
        else:
            st.image("https://img.icons8.com/color/96/verified-badge.png", width=70)
            
        st.title("Gestão MAQ")
        st.caption("🔒 Acesso Restrito ao Sistema de Compliance e Treinamentos")
        
        with st.form("form_login"):
            user_input = st.text_input("Usuário / Login")
            pass_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("🔑 Entrar no Sistema", use_container_width=True)
            
            if btn_login:
                with conn.cursor() as c:
                    c.execute("SELECT login, nome, perfil FROM usuarios WHERE login=%s AND senha=%s", (user_input.strip(), pass_input.strip()))
                    res = c.fetchone()
                
                if res:
                    st.session_state["usuario_logado"] = res[0]
                    st.session_state["nome_usuario"] = res[1]
                    st.session_state["perfil_usuario"] = res[2]
                    registrar_log(res[1], "LOGIN", f"Usuário {res[0]} efetuou login com perfil {res[2]}")
                    st.success(f"Bem-vindo(a), {res[1]}!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")
                    
        st.info("💡 **Acesso Padrão:** Admin: `admin` / `admin123` | Auditor: `auditor` / `auditor123` | Gestor: `gestor` / `gestor123`")
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
        
    ano_atual = datetime.date.today().year
    anos_disponiveis = [ano_atual - 1, ano_atual, ano_atual + 1]
    ano_exercicio = st.selectbox("📅 Exercício Anual do Sistema:", anos_disponiveis, index=1)
    
    st.divider()
    
    opcoes = ["📊 Dashboard Executivo", "👤 Visão do Colaborador", "📈 Evolução por Treinamento"]
    
    if perfil in ["Admin", "Gestor"]:
        opcoes.extend(["✍️ Lançar Treinamento", "📜 Certificados & Presença"])
        
    opcoes.append("📂 Relatórios p/ Auditoria")
    
    if perfil == "Admin":
        opcoes.extend(["👥 Gestão de Colaboradores", "📚 Catálogo de Treinamentos", "🎯 Matriz por Cargo (LNT)", "🔑 Gestão de Usuários", "💰 Gestão Orçamentária", "📜 Logs de Auditoria"])
    elif perfil == "Auditor":
        opcoes.extend(["📜 Logs de Auditoria", "📚 Catálogo de Treinamentos"])
        
    for opt in opcoes:
        if st.button(opt, use_container_width=True):
            st.session_state["pagina"] = opt
            st.rerun()

pagina = st.session_state["pagina"]

# -------------------------------------------------------------------
# GERADORES DE PDF E ELEMENTOS GRÁFICOS
# -------------------------------------------------------------------
def criar_selo_oficial():
    d = Drawing(85, 85)
    d.add(Circle(42, 42, 38, fillColor=colors.HexColor('#D97706'), strokeColor=colors.HexColor('#B45309'), strokeWidth=2))
    d.add(Circle(42, 42, 31, fillColor=colors.HexColor('#0F172A'), strokeColor=colors.HexColor('#F59E0B'), strokeWidth=1.5))
    d.add(String(42, 39, "OFICIAL", textAnchor='middle', fontName='Helvetica-Bold', fontSize=9, fillColor=colors.white))
    d.add(String(42, 51, "★ ★ ★", textAnchor='middle', fontName='Helvetica-Bold', fontSize=8, fillColor=colors.HexColor('#F59E0B')))
    d.add(String(42, 28, "COMPLIANCE", textAnchor='middle', fontName='Helvetica-Bold', fontSize=6, fillColor=colors.HexColor('#F59E0B')))
    return d

def desenhar_moldura_certificado(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#0F172A'))
    canvas.setLineWidth(4)
    canvas.rect(20, 20, doc.pagesize[0] - 40, doc.pagesize[1] - 40)
    canvas.setStrokeColor(colors.HexColor('#D97706'))
    canvas.setLineWidth(1.5)
    canvas.rect(26, 26, doc.pagesize[0] - 52, doc.pagesize[1] - 52)
    canvas.restoreState()

def gerar_pdf_prontuario(colab_info, df_realizados, total_mapeados, ano):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    logo_file = carregar_logo_empresa()
    if logo_file:
        try:
            img = Image(logo_file, width=140, height=45)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))
        except: pass
            
    story.append(Paragraph("<b>SISTEMA DE GESTÃO DE TREINAMENTOS - MAQ</b>", ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=1)))
    story.append(Paragraph(f"Prontuário Individual de Capacitação - Exercício {ano}", ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.HexColor('#64748B'), alignment=1)))
    story.append(Spacer(1, 15))
    
    dados_colab = [
        [Paragraph(f"<b>Nome:</b> {colab_info['nome']}", styles['Normal']), Paragraph(f"<b>Cargo:</b> {colab_info['cargo'] or 'N/A'}", styles['Normal'])],
        [Paragraph(f"<b>Departamento:</b> {colab_info['departamento']}", styles['Normal']), Paragraph(f"<b>Gestor:</b> {colab_info['gestor'] or 'N/A'}", styles['Normal'])],
        [Paragraph(f"<b>E-mail:</b> {colab_info['email'] or 'N/A'}", styles['Normal']), Paragraph(f"<b>Data Emissão:</b> {datetime.date.today().strftime('%d/%m/%Y')}", styles['Normal'])]
    ]
    t_info = Table(dados_colab, colWidths=[270, 270])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("<b>HISTÓRICO DE TREINAMENTOS CUMPRIDOS NO EXERCÍCIO</b>", ParagraphStyle('NormalBold', parent=styles['Normal'], fontSize=10, leading=12, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 5))
    
    headers = ["Treinamento / Norma", "Carga Horária", "Data Realização", "Validade", "Status"]
    table_data = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in headers]]
    
    if not df_realizados.empty:
        for _, r in df_realizados.iterrows():
            dt_r = pd.to_datetime(r['datarealizacao']).strftime('%d/%m/%Y')
            dt_v = (pd.to_datetime(r['datarealizacao']) + pd.DateOffset(months=r['validademeses'])).strftime('%d/%m/%Y')
            table_data.append([
                Paragraph(str(r['treinamento']), styles['Normal']),
                Paragraph(f"{r['horas']}h", styles['Normal']),
                Paragraph(dt_r, styles['Normal']),
                Paragraph(dt_v, styles['Normal']),
                Paragraph("CONFORME", styles['Normal'])
            ])
    else:
        table_data.append([Paragraph("Nenhum registro encontrado para este ano.", styles['Normal']), "", "", "", ""])
        
    t_treinos = Table(table_data, colWidths=[200, 70, 90, 90, 90])
    t_treinos.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_treinos)
    story.append(Spacer(1, 30))
    story.append(Paragraph("___________________________________ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ___________________________________", styles['Normal']))
    story.append(Paragraph("Assinatura do Colaborador &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Assinatura do Responsável RH", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def gerar_pdf_certificado(colab_nome, colab_cargo, curso_nome, carga_horaria, data_realizacao, aplicador_nome="Aplicador Técnico", aplicador_cargo="Aplicador do Treinamento"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=45,
        leftMargin=45,
        topMargin=40,
        bottomMargin=35
    )
    story = []
    styles = getSampleStyleSheet()
    
    logo_file = carregar_logo_empresa()
    selo = criar_selo_oficial()
    
    if logo_file:
        try:
            img_logo = Image(logo_file, width=180, height=55)
            t_top = Table([[img_logo, selo]], colWidths=[530, 150])
        except:
            t_top = Table([["", selo]], colWidths=[530, 150])
    else:
        t_top = Table([["", selo]], colWidths=[530, 150])
        
    t_top.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_top)
    story.append(Spacer(1, 15))
    
    title_main = ParagraphStyle('CertMain', parent=styles['Heading1'], fontSize=34, leading=38, fontName='Helvetica-Bold', textColor=colors
