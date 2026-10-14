import streamlit as st
import pandas as pd
import datetime
import os
import io
import plotly.express as px
import psycopg2

# ReportLab para geração de PDFs oficiais
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, String

st.set_page_config(
    page_title="Sistema Enterprise de Gestão de Treinamentos - MAQ",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

UPLOADS_DIR = "evidencias"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# -------------------------------------------------------------------
# CONEXÃO COM O SUPABASE COM TRATAMENTO DE ERROS E SSL
# -------------------------------------------------------------------
def get_db_connection():
    try:
        if "postgres" in st.secrets and "db_url" in st.secrets["postgres"]:
            db_url = st.secrets["postgres"]["db_url"]
            # Garante que sslmode seja configurado
            if "sslmode" not in db_url:
                conn = psycopg2.connect(db_url, sslmode="require")
            else:
                conn = psycopg2.connect(db_url)
            return conn
        else:
            st.error("❌ A credencial 'db_url' não foi encontrada nos Secrets do Streamlit.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Supabase: {e}")
        st.info("💡 Verifique se a senha, a porta (6543) e o endereço no secrets.toml estão corretos.")
        st.stop()

def run_query(query, params=None):
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

def get_lista_departamentos():
    df_deptos = run_query("SELECT DISTINCT departamento FROM colaboradores WHERE departamento IS NOT NULL AND departamento != ''")
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
    with get_db_connection() as conn:
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
                with get_db_connection() as conn:
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
