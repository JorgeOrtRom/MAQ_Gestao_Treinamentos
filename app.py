import io
import os
from datetime import date, datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
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
import streamlit.components.v1 as components

# ==========================================
# 0. CONFIGURAÇÃO DE TEMA E APLICAÇÃO
# ==========================================
st.set_page_config(page_title="Gestão e Qualidade - Attend", layout="wide")

st.markdown(
    """
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f8f9fa; padding: 10px; border-radius: 10px; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }
        .stTabs [data-baseweb="tab"] { height: 42px; background-color: #ffffff; border-radius: 8px; border: 1px solid #dcdcdc; padding: 0 16px; font-weight: 600; color: #333333; box-shadow: 0 2px 4px rgba(0,0,0,0.04); transition: all 0.2s ease-in-out; }
        .stTabs [data-baseweb="tab"]:hover { background-color: #e9ecef; border-color: #1f4e79; color: #1f4e79; transform: translateY(-1px); }
        .stTabs [aria-selected="true"] { background-color: #1f4e79 !important; color: #ffffff !important; border-color: #1f4e79 !important; box-shadow: 0 4px 8px rgba(31, 78, 121, 0.3) !important; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚙️ Sistema Integrado de Gestão e Acompanhamento MAQ")
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))


def conectar_banco():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


# ==========================================
# GESTÃO DE CACHE GLOBAL DE MEMÓRIA DE SESSÃO
# ==========================================
def atualizar_cache_global():
    try:
        conn = conectar_banco()

        # Processos
        df_proc = pd.read_sql("SELECT * FROM processos ORDER BY id ASC", conn)
        mapa_proc = {}
        for col in df_proc.columns:
            c_low = col.lower()
            if c_low == 'id': mapa_proc[col] = 'ID'
            elif c_low in ['nome_do_processo', 'nome_processo']: mapa_proc[col] = 'Nome_do_Processo'
            elif c_low == 'status': mapa_proc[col] = 'Status'
            elif c_low in ['responsavel', 'responsaveis']: mapa_proc[col] = 'Responsavel'
            elif c_low in ['data_abertura', 'dataabertura']: mapa_proc[col] = 'Data_Abertura'
            elif c_low in ['criador_processo', 'criador']: mapa_proc[col] = 'Criador'
            else: mapa_proc[col] = col

        df_proc = df_proc.rename(columns=mapa_proc)
        for c in ['ID', 'Nome_do_Processo', 'Status', 'Responsavel', 'Data_Abertura', 'Criador']:
            if c not in df_proc.columns:
                df_proc[c] = ''

        st.session_state['df_processos'] = df_proc[
            ['ID', 'Nome_do_Processo', 'Status', 'Responsavel', 'Data_Abertura', 'Criador']
        ].copy()

        # Tarefas
        df_tar = pd.read_sql("SELECT * FROM tarefas_processo ORDER BY id ASC", conn)
        mapa_tar = {}
        for col in df_tar.columns:
            c_low = col.lower()
            if c_low == 'id': mapa_tar[col] = 'id'
            elif c_low == 'processo': mapa_tar[col] = 'processo'
            elif c_low == 'descricao_tarefa': mapa_tar[col] = 'descricao_tarefa'
            elif c_low == 'prazo': mapa_tar[col] = 'prazo'
            elif c_low == 'responsavel_tarefa': mapa_tar[col] = 'responsavel_tarefa'
            elif c_low == 'concluido': mapa_tar[col] = 'concluido'
            elif c_low == 'tipo_atividade': mapa_tar[col] = 'tipo_atividade'
            elif c_low == 'peso_tempo_pct': mapa_tar[col] = 'peso_tempo_pct'
            else: mapa_tar[col] = col

        st.session_state['df_tarefas'] = df_tar.rename(columns=mapa_tar).copy()

        # Usuários
        df_u = pd.read_sql("SELECT * FROM usuarios ORDER BY nome ASC", conn)
        mapa_usr = {}
        for col in df_u.columns:
            c_low = col.lower()
            if c_low == 'id': mapa_usr[col] = 'ID'
            elif c_low == 'nome': mapa_usr[col] = 'Nome'
            elif c_low == 'funcao': mapa_usr[col] = 'Função'
            elif c_low == 'perfil': mapa_usr[col] = 'Perfil'
            elif c_low == 'senha': mapa_usr[col] = 'Senha'
            else: mapa_usr[col] = col

        st.session_state['df_usuarios'] = df_u.rename(columns=mapa_usr).copy()

        conn.close()
    except Exception as e:
        print(f'Erro ao carregar cache global: {e}')


def carregar_lista_colaboradores():
    if 'df_usuarios' in st.session_state and not st.session_state['df_usuarios'].empty:
        return st.session_state['df_usuarios']['Nome'].tolist()
    return ['Jorge', 'Jéssica', 'Rafael', 'Gabrielly', 'Matheus Lima', 'Matheus Marassatti', 'Felipe']


def registrar_log(usuario, processo, acao, detalhes):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        cursor.execute(
            'INSERT INTO log_auditoria (usuario, processo, acao, detalhes, data_hora) VALUES (%s, %s, %s, %s, %s)',
            (usuario, processo, acao, detalhes, agora),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f'Erro ao registrar log: {e}')


if 'df_processos' not in st.session_state or st.session_state['df_processos'].empty:
    atualizar_cache_global()

df = st.session_state.get('df_processos', pd.DataFrame())
lista_colaboradores_geral = carregar_lista_colaboradores()

# ==========================================
# 1. CONTROLE DE ACESSO (LOGIN NA SIDEBAR)
# ==========================================
caminho_logo = os.path.join(DIRETORIO_ATUAL, 'Logo_Attend_ Ambiental.png')

if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['usuario_atual'] = ''
    st.session_state['perfil_atual'] = ''

with st.sidebar:
    if os.path.exists(caminho_logo):
        st.image(caminho_logo, use_container_width=True)
    else:
        st.markdown('### 🏢 Attend Ambiental')

    st.markdown('---')

    if not st.session_state['autenticado']:
        st.markdown('### 🔐 Identificação do Usuário')
        
        with st.form('form_login_sidebar', clear_on_submit=False):
            user_sel = st.selectbox('Selecione seu Nome:', lista_colaboradores_geral)
            senha_dig = st.text_input('Senha de Acesso:', type='password', key='field_pwd_input')
            btn_entrar = st.form_submit_button('🔑 Entrar no Sistema', type='primary', use_container_width=True)

        if btn_entrar:
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                cursor.execute('SELECT senha, perfil FROM usuarios WHERE nome = %s', (user_sel,))
                res = cursor.fetchone()
                conn.close()

                if res and res[0] == senha_dig:
                    st.session_state['autenticado'] = True
                    st.session_state['usuario_atual'] = user_sel
                    st.session_state['perfil_atual'] = res[1]
                    atualizar_cache_global()
                    st.success(f'Bem-vindo, {user_sel}!')
                    st.rerun()
                else:
                    st.error('Senha incorreta!')
            except Exception as e:
                st.error(f'Erro ao autenticar: {e}')
    else:
        st.markdown(f"👤 **Logado como:** {st.session_state['usuario_atual']}")
        st.markdown(f"🛡️ **Perfil:** {st.session_state['perfil_atual']}")

        if st.button('🚪 Sair / Trocar Usuário'):
            st.session_state['autenticado'] = False
            st.session_state['usuario_atual'] = ''
            st.session_state['perfil_atual'] = ''
            st.rerun()

    st.markdown('---')
    st.markdown('### 📌 Jornada Corporativa')
    st.markdown('Segunda a Sexta-feira<br>08:00 às 17:00 (1h de almoço)<br><b>7h úteis/dia (35h semanais)</b>', unsafe_allow_html=True)
    st.markdown('---')
    st.markdown('Ambiente Nuvem Seguro<br>PostgreSQL Supabase', unsafe_allow_html=True)

if not st.session_state['autenticado']:
    st.warning('⚠️ Por favor, faça o login na barra lateral esquerda para acessar o sistema.')
    st.stop()

perfil_usuario = st.session_state['perfil_atual']
nome_usuario = st.session_state['usuario_atual']

# ==========================================
# 2. FUNÇÃO DE GERAÇÃO DE RELATÓRIO PDF
# ==========================================
def gerar_pdf_robusto(proc_nome, dados_proc, df_ish, df_5w, df_pdca, df_pareto, df_tarefas, df_logs_proc):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elementos = []
    styles = getSampleStyleSheet()
    cor_primaria = colors.HexColor('#1f4e79')
    cor_cinza = colors.HexColor('#f2f2f2')

    estilo_titulo = ParagraphStyle('TituloDoc', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=15, textColor=cor_primaria, spaceAfter=4)
    estilo_texto = ParagraphStyle('TextoCorpo', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=colors.HexColor('#333333'))

    cabecalho_dados = []
    if os.path.exists(caminho_logo):
        img_logo = Image(caminho_logo, width=110, height=45)
        cabecalho_dados = [[img_logo, Paragraph(f"<b>RELATÓRIO EXECUTIVO GLOBAL DE QUALIDADE</b><br/><font size=8 color='#666666'>Processo: {proc_nome}</font>", estilo_titulo)]]
    else:
        cabecalho_dados = [[Paragraph(f"<b>RELATÓRIO EXECUTIVO GLOBAL DE QUALIDADE</b><br/><font size=8 color='#666666'>Processo: {proc_nome}</font>", estilo_titulo)]]

    tabela_cab = Table(cabecalho_dados, colWidths=[130, 404])
    tabela_cab.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    elementos.append(tabela_cab)

    meta_texto = f"<b>Responsável(is) Geral(is):</b> {dados_proc['Responsavel']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Status Atual:</b> {dados_proc['Status']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Abertura:</b> {dados_proc['Data_Abertura']}"
    tabela_meta = Table([[Paragraph(meta_texto, estilo_texto)]], colWidths=[534])
    tabela_meta.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), cor_cinza), ('PADDING', (0, 0), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc'))]))
    elementos.append(tabela_meta)
    elementos.append(Spacer(1, 6))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 3. INTERFACE (ABAS ORGANIZADAS)
# ==========================================
(
    aba_home,
    aba_rotina,
    aba_tarefas,
    aba_qualidade,
    aba_dashboard,
    aba_progresso,
    aba_rotinas_tempo,
    aba_orcamento,
    aba_auditoria,
    aba_usuarios,
    aba_filtro_usuario,
) = st.tabs([
    '🏠 HOME',
    '📋 CADASTRO DE PROCESSOS',
    '📝 TAREFAS E PRAZOS',
    '🛠️ FERRAMENTAS DA QUALIDADE',
    '📊 DASHBOARD',
    '📈 PROGRESSO',
    '♾️ TEMPO POR DEMANDA',
    '💰 CONTROLE ORÇAMENTO',
    '🛡️ AUDITORIA DO SISTEMA',
    '🔑 USUÁRIOS',
    '🔍 FILTRO POR COLABORADOR',
])

# ABA 0: HOME / DASHBOARD INDIVIDUAL E GERENCIAL
with aba_home:
    st.markdown(f"### 👋 Olá, **{nome_usuario}**! Seja bem-vindo(a).")
    st.caption(f"Perfil de Acesso: **{perfil_usuario}** | Data: **{date.today().strftime('%d/%m/%Y')}**")
    
    hoje = date.today()
    df_tar_global = st.session_state.get('df_tarefas', pd.DataFrame())
    df_proc_global = st.session_state.get('df_processos', pd.DataFrame())

    if perfil_usuario in ['Administrador', 'Visualizador']:
        lista_colab_home = ['Todos os Colaboradores'] + sorted(carregar_lista_colaboradores())
        colab_selecionado_home = st.selectbox(
            "🔍 **Filtrar visão do Painel por Colaborador:**",
            lista_colab_home,
            key='sel_colab_home_dash'
        )
    else:
        colab_selecionado_home = nome_usuario

    st.divider()

    if colab_selecionado_home == 'Todos os Colaboradores':
        df_proc_user = df_proc_global.copy()
        df_tar_user = df_tar_global.copy()
        titulo_escopo = "Visão Geral Corporativa (Todos)"
    else:
        df_proc_user = df_proc_global[
            df_proc_global['Responsavel'].apply(lambda x: colab_selecionado_home in [p.strip() for p in str(x).split(',')])
        ] if not df_proc_global.empty else pd.DataFrame()
        
        df_tar_user = df_tar_global[
            df_tar_global['responsavel_tarefa'] == colab_selecionado_home
        ] if not df_tar_global.empty else pd.DataFrame()
        titulo_escopo = f"Painel de: {colab_selecionado_home}"

    tot_tarefas = len(df_tar_user)
    tar_concluidas = len(df_tar_user[df_tar_user['concluido'] == 1]) if tot_tarefas > 0 else 0
    
    vencidas_list = []
    proximas_list = []
    
    if not df_tar_user.empty:
        for _, tr in df_tar_user[df_tar_user['concluido'] == 0].iterrows():
            if tr.get('tipo_atividade', 'Não-Rotina') == 'Não-Rotina':
                try:
                    dt_p = datetime.strptime(tr['prazo'], '%d/%m/%Y').date()
                    dias = (dt_p - hoje).days
                    if dias < 0:
                        vencidas_list.append(tr)
                    elif dias <= 3:
                        proximas_list.append((tr, dias))
                except:
                    pass

    proc_fila = len(df_proc_user[df_proc_user['Status'] == 'Na Fila']) if not df_proc_user.empty else 0
    proc_andamento = len(df_proc_user[df_proc_user['Status'] == 'Em Andamento']) if not df_proc_user.empty else 0

    st.markdown(f"#### 📌 Indicadores — `{titulo_escopo}`")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 Tarefas Vencidas", len(vencidas_list))
    m2.metric("🟡 Vencem em breve (≤3d)", len(proximas_list))
    m3.metric("⏳ Processos Na Fila", proc_fila)
    m4.metric("🔄 Proc. Em Andamento", proc_andamento)
    m5.metric("✅ Tarefas Concluídas", f"{tar_concluidas}/{tot_tarefas}")

    st.divider()

    col_alert1, col_alert2 = st.columns(2)

    with col_alert1:
        st.markdown(f"#### 🚨 Alertas de Tarefas (`{titulo_escopo}`)")
        if vencidas_list:
            st.error(f"⚠️ **{len(vencidas_list)}** tarefa(s) atrasada(s):")
            for item in vencidas_list:
                st.markdown(
                    f"• 🔴 **{item['descricao_tarefa']}**<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;*Processo:* `{item['processo']}` | *Resp:* `{item['responsavel_tarefa']}` | *Prazo:* `{item['prazo']}`",
                    unsafe_allow_html=True
                )
        else:
            st.success("🎉 Nenhuma tarefa vencida pendente!")

        if proximas_list:
            st.warning(f"⏰ **{len(proximas_list)}** tarefa(s) vencendo nos próximos 3 dias:")
            for item, dias in proximas_list:
                str_dias = "vence HOJE!" if dias == 0 else f"vence em {dias} dia(s)"
                st.markdown(
                    f"• 🟡 **{item['descricao_tarefa']}** — **{str_dias}**<br>"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;*Processo:* `{item['processo']}` | *Resp:* `{item['responsavel_tarefa']}` | *Prazo:* `{item['prazo']}`",
                    unsafe_allow_html=True
                )

    with col_alert2:
        st.markdown(f"#### 📋 Processos Pendentes (`{titulo_escopo}`)")
        if not df_proc_user.empty:
            df_proc_pendentes = df_proc_user[df_proc_user['Status'].isin(['Na Fila', 'Em Andamento'])]
            if not df_proc_pendentes.empty:
                for _, pr in df_proc_pendentes.iterrows():
                    badge_color = "🔴 Na Fila" if pr['Status'] == 'Na Fila' else "🔵 Em Andamento"
                    st.markdown(
                        f"• **{pr['Nome_do_Processo']}** — `{badge_color}`<br>"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;*Abertura:* {pr['Data_Abertura']} | *Responsáveis:* {pr['Responsavel']}",
                        unsafe_allow_html=True
                    )
            else:
                st.info("Nenhum processo pendente encontrado.")
        else:
            st.info("Nenhum processo cadastrado para a seleção atual.")

    st.divider()

    st.markdown(f"#### 📊 Gráficos Gerenciais — `{titulo_escopo}`")
    g_home1, g_home2 = st.columns(2)

    with g_home1:
        if not df_tar_user.empty:
            st.markdown("**Situação das Tarefas**")
            status_tar = []
            for _, tr in df_tar_user.iterrows():
                if tr['concluido'] == 1:
                    status_tar.append('Concluída')
                else:
                    try:
                        dt_p = datetime.strptime(tr['prazo'], '%d/%m/%Y').date()
                        dias = (dt_p - hoje).days
                        if dias < 0:
                            status_tar.append('Vencida')
                        elif dias <= 3:
                            status_tar.append('A Vencer (≤3d)')
                        else:
                            status_tar.append('Em Aberto')
                    except:
                        status_tar.append('Em Aberto')
            
            df_tar_user_plot = df_tar_user.copy()
            df_tar_user_plot['Status_Calculado'] = status_tar
            fig_pie_user = px.pie(
                df_tar_user_plot, 
                names='Status_Calculado', 
                hole=0.4,
                color='Status_Calculado',
                color_discrete_map={
                    'Concluída': '#5cb85c',
                    'Vencida': '#d9534f',
                    'A Vencer (≤3d)': '#f0ad4e',
                    'Em Aberto': '#1f4e79'
                }
            )
            fig_pie_user.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pie_user, use_container_width=True)
        else:
            st.caption("Sem tarefas cadastradas no filtro selecionado.")

    with g_home2:
        if not df_proc_user.empty:
            st.markdown("**Status dos Processos**")
            fig_bar_user = px.bar(
                df_proc_user['Status'].value_counts().reset_index(),
                x='Status',
                y='count',
                color='Status',
                text='count',
                color_discrete_map={
                    'Concluído': '#5cb85c',
                    'Em Andamento': '#5bc0de',
                    'Na Fila': '#d9534f'
                }
            )
            fig_bar_user.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20), showlegend=False, xaxis_title="", yaxis_title="Qtd")
            st.plotly_chart(fig_bar_user, use_container_width=True)
        else:
            st.caption("Sem processos cadastrados no filtro selecionado.")

# ABA 1: CADASTRO DE PROCESSOS (EDITÁVEL E PERSISTENTE VIA ST.DATA_EDITOR)
with aba_rotina:
    st.markdown('### 📋 Controle de Processos')
    st.info('ℹ️ **Edição Direta:** Altere o Status ou os Responsáveis diretamente na tabela abaixo e clique em Salvar.')

    col_topo1, col_topo2 = st.columns(2)
    with col_topo1:
        with st.expander('➕ Adicionar Novo Processo'):
            with st.form('form_novo', clear_on_submit=True):
                nome = st.text_input('Nome do Processo')
                resp_selecionados = st.multiselect(
                    'Responsáveis pelo Processo', lista_colaboradores_geral
                )
                if st.form_submit_button('Cadastrar'):
                    if nome.strip() and resp_selecionados:
                        try:
                            resp_str = ', '.join(resp_selecionados)
                            conn = conectar_banco()
                            cursor = conn.cursor()
                            cursor.execute(
                                'INSERT INTO processos (nome_do_processo, status,'
                                ' responsavel, data_abertura, criador_processo) VALUES (%s,'
                                ' %s, %s, %s, %s)',
                                (
                                    nome.strip().upper(),
                                    'Na Fila',
                                    resp_str,
                                    date.today().strftime('%d/%m/%Y'),
                                    nome_usuario,
                                ),
                            )
                            conn.commit()
                            conn.close()
                            atualizar_cache_global()
                            st.success('Processo cadastrado com sucesso!')
                            st.rerun()
                        except psycopg2.IntegrityError:
                            st.error('Já existe um processo com este nome.')

    with col_topo2:
        with st.expander('🗑️ Remover Processo'):
            if perfil_usuario != 'Administrador':
                st.warning('🔒 Apenas Administradores podem excluir processos.')
            else:
                with st.form('form_exc', clear_on_submit=True):
                    lista_procs = (
                        sorted(df['Nome_do_Processo'].tolist()) if not df.empty else []
                    )
                    proc_exc = st.selectbox(
                        'Selecione o Processo para excluir:', lista_procs
                    )
                    if st.form_submit_button('Confirmar Exclusão'):
                        if proc_exc:
                            conn = conectar_banco()
                            cursor = conn.cursor()
                            cursor.execute(
                                'DELETE FROM processos WHERE nome_do_processo = %s',
                                (proc_exc,),
                            )
                            conn.commit()
                            conn.close()
                            atualizar_cache_global()
                            st.success('Processo excluído!')
                            st.rerun()

    st.divider()

    df_proc_memoria = st.session_state.get('df_processos', pd.DataFrame())

    if not df_proc_memoria.empty:
        # Tabela editável nativa que segura o estado no cliente e evita reset de renderização
        df_editado = st.data_editor(
            df_proc_memoria,
            column_config={
                "ID": st.column_config.NumberColumn("ID", disabled=True),
                "Nome_do_Processo": st.column_config.TextColumn("Nome do Processo", disabled=True),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Na Fila", "Em Andamento", "Concluído"],
                    required=True
                ),
                "Responsavel": st.column_config.TextColumn("Responsáveis"),
                "Data_Abertura": st.column_config.TextColumn("Data de Abertura", disabled=True),
                "Criador": st.column_config.TextColumn("Criador", disabled=True),
            },
            hide_index=True,
            use_container_width=True,
            key="editor_tabela_processos"
        )

        if st.button("💾 Salvar Alterações na Tabela", type="primary"):
            try:
                conn = conectar_banco()
                cursor = conn.cursor()
                
                # Gravação em lote síncrona
                for _, row in df_editado.iterrows():
                    cursor.execute(
                        "UPDATE processos SET status = %s, responsavel = %s WHERE id = %s",
                        (row['Status'], row['Responsavel'], row['ID'])
                    )
                conn.commit()
                conn.close()
                
                # Atualização imediata na memória global da sessão
                st.session_state['df_processos'] = df_editado.copy()
                registrar_log(nome_usuario, "Geral", "Edição em Tabela", "Atualização em lote dos processos.")
                st.success("✅ Todas as alterações foram salvas e sincronizadas com o Dashboard!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar alterações no banco: {e}")

# ABA 2: TAREFAS E PRAZOS
with aba_tarefas:
    st.markdown('### 📝 Gestão de Tarefas, Prazos e Alertas de Vencimento')

    if df.empty:
        st.warning('Cadastre um processo na Aba 1 antes de gerenciar tarefas.')
    else:
        proc_t = st.selectbox(
            'Selecione o Processo para gerenciar as tarefas:',
            sorted(df['Nome_do_Processo'].unique()),
            key='sel_proc_tarefas',
        )
        
        df_tarefas_full = st.session_state.get('df_tarefas', pd.DataFrame())
        if not df_tarefas_full.empty:
            df_tarefas = df_tarefas_full[df_tarefas_full['processo'] == proc_t].copy()
            for _, t in df_tarefas.iterrows():
                t_id = t['id']
                t_desc = t['descricao_tarefa']
                t_conc = bool(t['concluido'])
                t_resp = t['responsavel_tarefa']

                pode_concluir = (perfil_usuario == 'Administrador' or nome_usuario == t_resp)

                with st.container(border=True):
                    col_check, col_info = st.columns([1, 7])
                    with col_check:
                        check_val = st.checkbox('OK', value=t_conc, key=f'chk_t_{t_id}', disabled=not pode_concluir)
                        if pode_concluir and check_val != t_conc:
                            conn = conectar_banco()
                            cursor = conn.cursor()
                            cursor.execute(
                                'UPDATE tarefas_processo SET concluido = %s WHERE id = %s',
                                (1 if check_val else 0, t_id),
                            )
                            conn.commit()
                            conn.close()
                            
                            st.session_state['df_tarefas'].loc[
                                st.session_state['df_tarefas']['id'] == t_id, 'concluido'
                            ] = 1 if check_val else 0
                            
                            st.rerun()
                    with col_info:
                        st.markdown(f"**{t_desc}** (Resp: `{t_resp}`)")

# ABA 3: FERRAMENTAS DA QUALIDADE
with aba_qualidade:
    st.markdown('### 🛠️ Registro, Edição e Histórico de Ferramentas de Qualidade')

# ABA 4: DASHBOARD GLOBAL & EXPORTAÇÃO EXCEL
with aba_dashboard:
    st.markdown('### 📊 Dashboard Matriz Hoshin & Exportação Geral')
    if not df.empty:
        total_proc = len(df)
        concluidos = len(df[df['Status'] == 'Concluído'])
        em_andamento = len(df[df['Status'] == 'Em Andamento'])
        na_fila = len(df[df['Status'] == 'Na Fila'])
        taxa_sucesso = (concluidos / total_proc * 100) if total_proc > 0 else 0

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric(label='📊 Total de Processos', value=total_proc)
        k2.metric(label='⏳ Na Fila', value=na_fila)
        k3.metric(label='🔄 Em Andamento', value=em_andamento)
        k4.metric(label='✅ Concluídos', value=concluidos)
        k5.metric(label='🎯 Taxa de Resolução', value=f'{taxa_sucesso:.1f}%')

# ABA 5: PROGRESSO DINÂMICO
with aba_progresso:
    st.markdown('### 📈 Progresso e Evolução com Base nas Tarefas Realizadas')

# ABA 6: CARGA DE TEMPO (%)
with aba_rotinas_tempo:
    st.markdown('### ♾️ Mapeamento de Esforço e Atividades que Mais Consomem Tempo')

# ABA 7: ORÇAMENTO & PLANEJAMENTO
with aba_orcamento:
    st.markdown('### 💰 Gestão e Planejamento Orçamentário do Setor')

# ABA 8: AUDITORIA E LOGS
with aba_auditoria:
    st.markdown('### 🛡️ Registro de Auditoria e Rastreabilidade')

# ABA 9: GESTÃO DE USUÁRIOS
with aba_usuarios:
    st.markdown('### 🔑 Gestão de Usuários, Cargos/Funções e Alteração de Senha')

# ABA 10: FILTRO POR COLABORADOR
with aba_filtro_usuario:
    st.markdown('### 🔍 Consulta e Filtro de Atividades por Colaborador')
