import streamlit as st
import pandas as pd
import sqlite3
import datetime
import os
import io
import plotly.express as px

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

def get_db_connection():
    return sqlite3.connect("treinamentos.db")

conn = get_db_connection()

# Cria as tabelas necessárias e adequa o banco de dados
def adequar_banco_dados():
    c = conn.cursor()
    
    # 1. Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            senha TEXT,
            nome TEXT,
            perfil TEXT
        )
    ''')
    
    # Insere usuários padrão caso a tabela esteja vazia
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (login, senha, nome, perfil) VALUES ('admin', 'admin123', 'Administrador', 'Admin')")
        c.execute("INSERT INTO usuarios (login, senha, nome, perfil) VALUES ('auditor', 'auditor123', 'Auditor Interno', 'Auditor')")
        c.execute("INSERT INTO usuarios (login, senha, nome, perfil) VALUES ('gestor', 'gestor123', 'Gestor de Área', 'Gestor')")
        conn.commit()

    # 2. Tabela de Colaboradores
    c.execute('''
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            departamento TEXT,
            cargo TEXT,
            gestor TEXT,
            genero TEXT,
            email TEXT
        )
    ''')

    # 3. Tabela de Treinamentos (Catálogo)
    c.execute('''
        CREATE TABLE IF NOT EXISTS treinamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_curso TEXT,
            carga_horaria REAL,
            frequencia TEXT,
            classificacao TEXT,
            custo_estimado REAL DEFAULT 0.0,
            aplicador_padrao TEXT,
            aplicador_cargo_padrao TEXT
        )
    ''')

    # 4. Tabela de Registros de Treinamento
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            treinamento_id INTEGER,
            data_realizacao TEXT,
            validade_meses INTEGER,
            status_planilha TEXT,
            arquivo_evidencia TEXT,
            arquivo_forms TEXT,
            instrutor_nome TEXT,
            aplicador_cargo TEXT,
            custo_real REAL DEFAULT 0.0
        )
    ''')

    # 5. Tabela de Matriz por Cargo (LNT)
    c.execute('''
        CREATE TABLE IF NOT EXISTS matriz_cargo_treinamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cargo TEXT,
            treinamento_id INTEGER
        )
    ''')

    # 6. Tabela de Logs de Auditoria
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            acao TEXT,
            detalhes TEXT
        )
    ''')

    # Garantia de colunas legadas em bancos preexistentes
    try: c.execute("ALTER TABLE registros ADD COLUMN arquivo_forms TEXT"); conn.commit()
    except sqlite3.OperationalError: pass
    
    try: c.execute("ALTER TABLE registros ADD COLUMN instrutor_nome TEXT"); conn.commit()
    except sqlite3.OperationalError: pass
    
    try: c.execute("ALTER TABLE registros ADD COLUMN aplicador_cargo TEXT"); conn.commit()
    except sqlite3.OperationalError: pass

    try: c.execute("ALTER TABLE treinamentos ADD COLUMN aplicador_padrao TEXT"); conn.commit()
    except sqlite3.OperationalError: pass

    try: c.execute("ALTER TABLE treinamentos ADD COLUMN aplicador_cargo_padrao TEXT"); conn.commit()
    except sqlite3.OperationalError: pass

adequar_banco_dados()

def get_lista_departamentos():
    df_deptos = pd.read_sql_query("SELECT DISTINCT departamento FROM colaboradores WHERE departamento IS NOT NULL AND departamento != ''", conn)
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
    c = conn.cursor()
    c.execute("INSERT INTO logs_auditoria (usuario, acao, detalhes) VALUES (?, ?, ?)", (str(usuario), str(acao), str(detalhes)))
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
                c = conn.cursor()
                c.execute("SELECT login, nome, perfil FROM usuarios WHERE login=? AND senha=?", (user_input.strip(), pass_input.strip()))
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
# MENU LATERAL COM LOGO E SELETOR DE ANO DE EXERCÍCIO
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
# ELEMENTOS GRÁFICOS E MOLDURA DO CERTIFICADO
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

# -------------------------------------------------------------------
# GERADORES DE PDF
# -------------------------------------------------------------------
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
            dt_r = pd.to_datetime(r['DataRealizacao']).strftime('%d/%m/%Y')
            dt_v = (pd.to_datetime(r['DataRealizacao']) + pd.DateOffset(months=r['ValidadeMeses'])).strftime('%d/%m/%Y')
            table_data.append([
                Paragraph(str(r['Treinamento']), styles['Normal']),
                Paragraph(f"{r['Horas']}h", styles['Normal']),
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
    
    title_main = ParagraphStyle('CertMain', parent=styles['Heading1'], fontSize=34, leading=38, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'), alignment=1)
    story.append(Paragraph("CERTIFICADO DE CONCLUSÃO", title_main))
    story.append(Spacer(1, 15))
    
    sub_title_style = ParagraphStyle('CertSubTitle', parent=styles['Normal'], fontSize=13, leading=16, fontName='Helvetica-Oblique', textColor=colors.HexColor('#475569'), alignment=1)
    story.append(Paragraph("confere o presente certificado a", sub_title_style))
    story.append(Spacer(1, 12))
    
    nome_style = ParagraphStyle('CertNome', parent=styles['Heading1'], fontSize=28, leading=32, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E3A8A'), alignment=1)
    story.append(Paragraph(f"{str(colab_nome).upper()}", nome_style))
    story.append(Spacer(1, 15))
    
    dt_f = pd.to_datetime(data_realizacao).strftime('%d/%m/%Y')
    desc_text = f"pela conclusão com êxito do treinamento de <b>{curso_nome}</b>, realizado em <b>{dt_f}</b>, com carga horária total de <b>{carga_horaria} horas</b>, em conformidade com as normas de segurança e gestão da Attend Ambiental."
    desc_style = ParagraphStyle('CertDesc', parent=styles['Normal'], fontSize=11.5, leading=17, textColor=colors.HexColor('#334155'), alignment=1)
    story.append(Paragraph(desc_text, desc_style))
    story.append(Spacer(1, 35))
    
    ass_nome_style = ParagraphStyle('AssNome', parent=styles['Normal'], fontSize=9.5, leading=11, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'), alignment=1)
    ass_cargo_style = ParagraphStyle('AssCargo', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#64748B'), alignment=1)
    
    colab_cargo_txt = colab_cargo if colab_cargo else "Analista"
    ap_nome_txt = aplicador_nome if aplicador_nome else "Aplicador Técnico"
    ap_cargo_txt = aplicador_cargo if aplicador_cargo else "Aplicador do Treinamento"
    
    linha = Paragraph("___________________________________", ass_cargo_style)
    
    dados_ass = [
        [linha, linha, linha],
        [
            Paragraph(f"<b>{ap_nome_txt}</b>", ass_nome_style),
            Paragraph("<b>Jéssica Rocha</b>", ass_nome_style),
            Paragraph(f"<b>{colab_nome}</b>", ass_nome_style)
        ],
        [
            Paragraph(f"{ap_cargo_txt}", ass_cargo_style),
            Paragraph("Gestora de MAQ / SSO", ass_cargo_style),
            Paragraph(f"{colab_cargo_txt}", ass_cargo_style)
        ]
    ]
    
    t_ass = Table(dados_ass, colWidths=[225, 230, 225])
    t_ass.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 2)
    ]))
    story.append(t_ass)
    
    doc.build(story, onFirstPage=desenhar_moldura_certificado)
    buffer.seek(0)
    return buffer

def gerar_pdf_lista_presenca(curso_nome, carga_horaria, departamento_nome, lista_colabs, ano):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    sub_style = ParagraphStyle('LPSub', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.HexColor('#475569'))
    
    logo_file = carregar_logo_empresa()
    if logo_file:
        try:
            img = Image(logo_file, width=140, height=45)
            img.hAlign = 'CENTER'
            story.append(img)
            story.append(Spacer(1, 10))
        except: pass

    story.append(Paragraph(f"<b>LISTA DE PRESENÇA OFICIAL DE TREINAMENTO ({ano}) - MAQ</b>", ParagraphStyle('LPTitle', parent=styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), alignment=1)))
    story.append(Spacer(1, 10))
    
    header_data = [
        [Paragraph(f"<b>Treinamento:</b> {curso_nome}", sub_style), Paragraph(f"<b>Carga Horária:</b> {carga_horaria}h", sub_style)],
        [Paragraph(f"<b>Setor/Departamento:</b> {departamento_nome}", sub_style), Paragraph(f"<b>Data de Aplicação:</b> ____/____/{ano}", sub_style)],
        [Paragraph("<b>Gestora responsável MAQ:</b> Jéssica Rocha", sub_style), Paragraph("<b>Aplicador:</b> ________________________", sub_style)]
    ]
    t_head = Table(header_data, colWidths=[270, 270])
    t_head.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 15))
    
    headers = ["#", "Nome do Colaborador", "Cargo / Função", "Assinatura do Participante"]
    table_rows = [[Paragraph(f"<b>{h}</b>", sub_style) for h in headers]]
    
    for idx, c in enumerate(lista_colabs, start=1):
        table_rows.append([
            Paragraph(str(idx), sub_style),
            Paragraph(str(c['nome']), sub_style),
            Paragraph(str(c['cargo'] or 'Operacional'), sub_style),
            Paragraph("", sub_style)
        ])
        
    t_list = Table(table_rows, colWidths=[30, 200, 130, 180])
    t_list.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_list)
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Visto da Gestão MAQ (Jéssica Rocha):</b> ___________________________ &nbsp;&nbsp;&nbsp;&nbsp; <b>Data:</b> ____/____/{ano}", sub_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# -------------------------------------------------------------------
# 1. DASHBOARD EXECUTIVO
# -------------------------------------------------------------------
if pagina == "📊 Dashboard Executivo":
    st.markdown(f'<div class="main-header">📊 Dashboard Geral de Performance e Compliance Executivo ({ano_exercicio})</div>', unsafe_allow_html=True)
    
    query = '''
        SELECT 
            c.nome AS Colaborador,
            c.departamento AS Departamento,
            t.nome_curso AS Treinamento,
            t.carga_horaria AS Horas,
            t.classificacao AS Classificacao,
            r.data_realizacao AS DataRealizacao,
            r.validade_meses AS ValidadeMeses,
            r.arquivo_evidencia AS Evidencia
        FROM registros r
        JOIN colaboradores c ON r.colaborador_id = c.id
        JOIN treinamentos t ON r.treinamento_id = t.id
        WHERE strftime('%Y', r.data_realizacao) = ?
    '''
    df = pd.read_sql_query(query, conn, params=(str(ano_exercicio),))
    df_colabs_total = pd.read_sql_query("SELECT COUNT(*) as total FROM colaboradores", conn)['total'].iloc[0]
    
    if df.empty:
        st.info(f"💡 Nenhum registro cadastrado no banco de dados para o ano de {ano_exercicio}.")
    else:
        df['DataRealizacao'] = pd.to_datetime(df['DataRealizacao'])
        df['DataVencimento'] = df.apply(lambda row: row['DataRealizacao'] + pd.DateOffset(months=row['ValidadeMeses']), axis=1)
        hoje = pd.to_datetime(datetime.date.today())
        df['DiasParaVencer'] = (df['DataVencimento'] - hoje).dt.days
        
        def set_status(dias):
            if dias < 0: return "🔴 Vencido (Não Conforme)"
            elif dias <= 30: return "🟡 Vencerá em 30 Dias"
            else: return "🟢 Conforme / Em Dia"
                
        df['Status'] = df['DiasParaVencer'].apply(set_status)
        
        c1, c2, c3 = st.columns(3)
        with c1: depto_sel = st.multiselect("Filtrar Departamento", options=df['Departamento'].unique(), default=df['Departamento'].unique())
        with c2: classif_sel = st.multiselect("Filtrar Classificação", options=df['Classificacao'].unique(), default=df['Classificacao'].unique())
        with c3: status_sel = st.multiselect("Filtrar Status", options=df['Status'].unique(), default=df['Status'].unique())
            
        df_filtered = df[(df['Departamento'].isin(depto_sel)) & (df['Classificacao'].isin(classif_sel)) & (df['Status'].isin(status_sel))]
        
        st.divider()
        k1, k2, k3, k4, k5 = st.columns(5)
        total_horas = df_filtered['Horas'].sum()
        conformes = len(df_filtered[df_filtered['Status'] == "🟢 Conforme / Em Dia"])
        nao_conformes = len(df_filtered[df_filtered['Status'] == "🔴 Vencido (Não Conforme)"])
        tx_conformidade = (conformes / len(df_filtered) * 100) if len(df_filtered) > 0 else 0.0
        
        k1.metric("👥 Colaboradores", df_colabs_total)
        k2.metric("⏱️ Horas Capacitadas", f"{total_horas:.1f}h")
        k3.metric("📈 Taxa Conformidade", f"{tx_conformidade:.1f}%")
        k4.metric("🟢 Em Dia", conformes)
        k5.metric("🔴 Vencidos", nao_conformes, delta_color="inverse")
        
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📊 Compliance por Status")
            fig_status = px.pie(df_filtered, names='Status', hole=0.4, color='Status', color_discrete_map={"🟢 Conforme / Em Dia": "#10B981", "🟡 Vencerá em 30 Dias": "#F59E0B", "🔴 Vencido (Não Conforme)": "#EF4444"})
            st.plotly_chart(fig_status, use_container_width=True)
        with col_g2:
            st.subheader(f"🏢 Horas Capacitadas em {ano_exercicio} por Setor")
            df_depto = df_filtered.groupby('Departamento')['Horas'].sum().reset_index()
            fig_bar = px.bar(df_depto, x='Departamento', y='Horas', text_auto='.1f', color='Departamento')
            st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------------
# 2. VISÃO DO COLABORADOR
# -------------------------------------------------------------------
elif pagina == "👤 Visão do Colaborador":
    st.markdown(f'<div class="main-header">👤 Prontuário Individual e Matriz de Participação ({ano_exercicio})</div>', unsafe_allow_html=True)
    
    df_colabs = pd.read_sql_query("SELECT id, nome, departamento, cargo, gestor, genero, email FROM colaboradores ORDER BY nome", conn)
    
    if df_colabs.empty:
        st.warning("Nenhum colaborador cadastrado.")
    else:
        colab_nome = st.selectbox("🔎 Selecione o Colaborador:", df_colabs['nome'].tolist())
        colab_info = df_colabs[df_colabs['nome'] == colab_nome].iloc[0]
        cid = int(colab_info['id'])
        
        query_lnt = '''
            SELECT t.id, t.nome_curso, t.carga_horaria, t.frequencia, t.classificacao, t.aplicador_padrao, t.aplicador_cargo_padrao 
            FROM treinamentos t
            JOIN matriz_cargo_treinamento m ON t.id = m.treinamento_id
            WHERE m.cargo = ?
        '''
        df_lnt_cargo = pd.read_sql_query(query_lnt, conn, params=(colab_info['cargo'],))
        if df_lnt_cargo.empty:
            df_lnt_cargo = pd.read_sql_query("SELECT id, nome_curso, carga_horaria, frequencia, classificacao, aplicador_padrao, aplicador_cargo_padrao FROM treinamentos", conn)
            
        total_mapeados = len(df_lnt_cargo)
        
        query_ind = '''
            SELECT 
                t.id AS TreinamentoID, t.nome_curso AS Treinamento, t.classificacao AS Classificacao,
                t.carga_horaria AS Horas, r.data_realizacao AS DataRealizacao,
                r.validade_meses AS ValidadeMeses, r.arquivo_evidencia AS Evidencia,
                r.arquivo_forms AS Forms, r.instrutor_nome AS Instrutor, r.aplicador_cargo AS AplicadorCargo
            FROM registros r
            JOIN treinamentos t ON r.treinamento_id = t.id
            WHERE r.colaborador_id = ? AND strftime('%Y', r.data_realizacao) = ?
        '''
        df_realizados = pd.read_sql_query(query_ind, conn, params=(cid, str(ano_exercicio)))
        
        qtd_realizados = len(df_realizados)
        qtd_pendentes = max(0, total_mapeados - qtd_realizados)
        pct_concluido = (qtd_realizados / total_mapeados * 100) if total_mapeados > 0 else 0.0
        horas_acumuladas = df_realizados['Horas'].sum() if not df_realizados.empty else 0.0
        
        c_f1, c_f2 = st.columns([3, 1])
        with c_f1:
            st.markdown(f"""
            <div class="colab-card">
                <h3 style="margin-top:0;">👤 <b>{colab_info['nome']}</b></h3>
                <p style="margin-bottom:5px;">💼 <b>Cargo:</b> {colab_info['cargo'] or 'Não informado'} &nbsp;|&nbsp; 👔 <b>Gestor Direto:</b> {colab_info['gestor'] or 'Não informado'}</p>
                <p style="margin-bottom:0;">🏢 <b>Departamento:</b> {colab_info['departamento']} &nbsp;|&nbsp; ✉️ <b>E-mail:</b> {colab_info['email'] or 'N/A'}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with c_f2:
            st.write(f"📄 **Prontuário {ano_exercicio}**")
            pdf_bytes = gerar_pdf_prontuario(colab_info, df_realizados, total_mapeados, ano_exercicio)
            st.download_button(
                label="🖨️ Baixar Prontuário PDF",
                data=pdf_bytes,
                file_name=f"Prontuario_{colab_info['nome'].replace(' ', '_')}_{ano_exercicio}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        st.subheader(f"📊 Evolução de Treinamentos Mapeados ({ano_exercicio})")
        st.write(f"**Progresso:** `{qtd_realizados}` de `{total_mapeados}` cursos exigidos concluídos em {ano_exercicio} (**{pct_concluido:.1f}%**)")
        st.progress(min(pct_concluido / 100.0, 1.0))
        
        kc1, kc2, k3, kc4 = st.columns(4)
        kc1.metric("🎯 Exigidos p/ Cargo", f"{total_mapeados} Cursos")
        kc2.metric("✅ Concluídos no Ano", f"{qtd_realizados} Cursos")
        kc3.metric("⏳ Pendentes no Ano", f"{qtd_pendentes} Cursos")
        kc4.metric("⏱ Horas Cumpridas", f"{horas_acumuladas:.1f}h")
        
        st.divider()
        st.subheader("📋 Gestão Individual por Treinamento (Status, Dados do Aplicador e Uploads)")
        
        for _, r_t in df_lnt_cargo.iterrows():
            tid = r_t['id']
            nome_curso = r_t['nome_curso']
            ch_val = r_t['carga_horaria']
            
            reg_filtrado = df_realizados[df_realizados['TreinamentoID'] == tid]
            is_concluido = not reg_filtrado.empty
            reg_info = reg_filtrado.iloc[0] if is_concluido else None
            
            with st.form(key=f"form_colab_{cid}_{tid}"):
                st.markdown(f"#### 📚 {nome_curso} ({ch_val}h - {r_t['classificacao']})")
                col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns([2, 2, 2, 2, 2.5])
                
                with col_c1:
                    novo_status = st.selectbox(
                        "Status",
                        options=["🔴 Pendente", "🟢 Concluído"],
                        index=1 if is_concluido else 0,
                        key=f"status_{cid}_{tid}"
                    )
                    
                with col_c2:
                    dt_def = pd.to_datetime(reg_info['DataRealizacao']).date() if is_concluido else datetime.date.today()
                    nova_data = st.date_input("Data Aplicação", value=dt_def, key=f"data_{cid}_{tid}")
                    
                with col_c3:
                    inst_def = reg_info['Instrutor'] if (is_concluido and reg_info['Instrutor']) else (r_t['aplicador_padrao'] or "Aplicador Técnico")
                    nome_aplicador = st.text_input("Nome do Aplicador", value=inst_def, key=f"inst_{cid}_{tid}")
                    
                with col_c4:
                    cargo_def = reg_info['AplicadorCargo'] if (is_concluido and 'AplicadorCargo' in reg_info and reg_info['AplicadorCargo']) else (r_t['aplicador_cargo_padrao'] or "Aplicador do Treinamento")
                    cargo_aplicador = st.text_input("Cargo do Aplicador", value=cargo_def, key=f"acargo_{cid}_{tid}")
                    
                with col_c5:
                    up_f = st.file_uploader("📎 Anexar Forms / Lista", type=["pdf", "png", "jpg"], key=f"up_{cid}_{tid}")
                
                btn_salvar = st.form_submit_button(f"💾 Salvar Atualização de '{nome_curso}'", use_container_width=True)

                if btn_salvar:
                    c = conn.cursor()
                    dt_str = nova_data.strftime('%Y-%m-%d')
                    
                    if novo_status == "🟢 Concluído":
                        nome_forms_salvo = reg_info['Forms'] if (is_concluido and reg_info['Forms']) else "Sem anexo"
                        if up_f is not None:
                            nome_forms_salvo = f"Forms_{cid}_{tid}_{dt_str}_{up_f.name}"
                            with open(os.path.join(UPLOADS_DIR, nome_forms_salvo), "wb") as f:
                                f.write(up_f.getbuffer())
                                
                        nome_cert_auto = f"Certificado_AUTO_{cid}_{tid}_{dt_str}.pdf"
                        cert_path_auto = os.path.join(UPLOADS_DIR, nome_cert_auto)
                        pdf_bytes_cert = gerar_pdf_certificado(
                            colab_nome=colab_info['nome'],
                            colab_cargo=colab_info['cargo'],
                            curso_nome=nome_curso,
                            carga_horaria=ch_val,
                            data_realizacao=dt_str,
                            aplicador_nome=nome_aplicador,
                            aplicador_cargo=cargo_aplicador
                        )
                        with open(cert_path_auto, "wb") as f:
                            f.write(pdf_bytes_cert.getvalue())
                            
                        if not is_concluido:
                            c.execute('''
                                INSERT INTO registros (colaborador_id, treinamento_id, data_realizacao, validade_meses, status_planilha, arquivo_evidencia, arquivo_forms, instrutor_nome, aplicador_cargo, custo_real)
                                VALUES (?, ?, ?, 12, 'Concluído', ?, ?, ?, ?, 0.0)
                            ''', (cid, tid, dt_str, nome_cert_auto, nome_forms_salvo, nome_aplicador, cargo_aplicador))
                        else:
                            c.execute("UPDATE registros SET data_realizacao=?, arquivo_evidencia=?, arquivo_forms=?, instrutor_nome=?, aplicador_cargo=? WHERE colaborador_id=? AND treinamento_id=? AND strftime('%Y', data_realizacao)=?", (dt_str, nome_cert_auto, nome_forms_salvo, nome_aplicador, cargo_aplicador, cid, tid, str(ano_exercicio)))
                            
                        conn.commit()
                        st.success(f"🎉 Treinamento '{nome_curso}' atualizado e salvo no banco de dados!")
                        st.rerun()
                        
                    elif novo_status == "🔴 Pendente" and is_concluido:
                        if reg_info['Evidencia']:
                            p_ev = os.path.join(UPLOADS_DIR, str(reg_info['Evidencia']))
                            if os.path.exists(p_ev): os.remove(p_ev)
                        if reg_info['Forms'] and reg_info['Forms'] != "Sem anexo":
                            p_f = os.path.join(UPLOADS_DIR, str(reg_info['Forms']))
                            if os.path.exists(p_f): os.remove(p_f)
                            
                        c.execute("DELETE FROM registros WHERE colaborador_id=? AND treinamento_id=? AND strftime('%Y', data_realizacao)=?", (cid, tid, str(ano_exercicio)))
                        conn.commit()
                        registrar_log(st.session_state["nome_usuario"], "EXCLUSÃO DE REGISTRO", f"Removido treinamento ID {tid} do colaborador ID {cid}")
                        st.warning(f"🗑️ Registro e Certificado de '{nome_curso}' foram excluídos!")
                        st.rerun()

            if is_concluido and reg_info is not None:
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    cert_file = reg_info['Evidencia']
                    cert_path = os.path.join(UPLOADS_DIR, str(cert_file))
                    if os.path.exists(cert_path):
                        with open(cert_path, "rb") as f_c:
                            st.download_button("🎓 Baixar Certificado", f_c.read(), file_name=str(cert_file), key=f"dl_c_{cid}_{tid}")
                with col_dl2:
                    forms_file = reg_info['Forms']
                    if forms_file and forms_file not in ["Sem anexo", "None", "nan"]:
                        forms_path = os.path.join(UPLOADS_DIR, str(forms_file))
                        if os.path.exists(forms_path):
                            with open(forms_path, "rb") as f_f:
                                st.download_button("📎 Baixar Forms/Lista", f_f.read(), file_name=str(forms_file), key=f"dl_f_{cid}_{tid}")
            
            st.divider()

# -------------------------------------------------------------------
# 3. LANÇAR TREINAMENTO
# -------------------------------------------------------------------
elif pagina == "✍️ Lançar Treinamento":
    st.markdown('<div class="main-header">✍️ Registro de Treinamento e Emissão Automática de Certificado</div>', unsafe_allow_html=True)
    df_colab = pd.read_sql_query("SELECT id, nome, cargo, departamento FROM colaboradores ORDER BY nome", conn)
    df_treino = pd.read_sql_query("SELECT id, nome_curso, carga_horaria, frequencia, custo_estimado, aplicador_padrao, aplicador_cargo_padrao FROM treinamentos ORDER BY nome_curso", conn)
    
    if df_colab.empty or df_treino.empty:
        st.warning("Cadastre colaboradores e treinamentos antes.")
    else:
        with st.form("form_registro_evidencia"):
            c1, c2 = st.columns(2)
            with c1:
                colab_dict = {f"{r['nome']} ({r['departamento']})": (r['id'], r['nome'], r['cargo']) for _, r in df_colab.iterrows()}
                colab_sel = st.selectbox("Selecione o Colaborador", options=list(colab_dict.keys()))
                dt_realizacao = st.date_input("Data de Aplicação", datetime.date.today())
