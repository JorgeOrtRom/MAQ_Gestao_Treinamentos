from datetime import datetime
import pandas as pd
import sqlite3
import streamlit as st
from supabase import create_client

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E CONEXÃO SUPABASE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MAQ - Gestão de Treinamentos",
    page_icon="📚",
    layout="wide",
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def limpar_valor(val):
  """Auxiliar para converter NaNs do pandas em None (null no Supabase)."""
  if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", ""]:
    return None
  return str(val).strip()


# -----------------------------------------------------------------------------
# 2. FUNÇÕES DE BUSCA DE DADOS (SUPABASE)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def carregar_colaboradores():
  res = (
      supabase.table("colaboradores")
      .select("*")
      .order("nome", desc=False)
      .execute()
  )
  df = pd.DataFrame(res.data)
  if not df.empty:
    df = df.where(pd.notnull(df), None)
  return df


@st.cache_data(ttl=5)
def carregar_treinamentos():
  res = (
      supabase.table("treinamentos")
      .select("*")
      .order("nome_curso", desc=False)
      .execute()
  )
  df = pd.DataFrame(res.data)
  if not df.empty:
    df = df.where(pd.notnull(df), None)
  return df


@st.cache_data(ttl=5)
def carregar_registros():
  res = supabase.table("registros").select("*").execute()
  df = pd.DataFrame(res.data)
  if not df.empty:
    df = df.where(pd.notnull(df), None)
  return df


# -----------------------------------------------------------------------------
# 3. INTERFACE E NAVEGAÇÃO
# -----------------------------------------------------------------------------
st.title("📚 MAQ - Sistema de Gestão de Treinamentos")

menu = st.sidebar.radio(
    "Navegação",
    [
        "👥 Gestão de Colaboradores",
        "📊 Dashboard Executivo",
        "📚 Catálogo de Treinamentos",
    ],
)

df_colab = carregar_colaboradores()
df_treino = carregar_treinamentos()
df_reg = carregar_registros()

# -----------------------------------------------------------------------------
# MODULO 1: GESTÃO DE COLABORADORES
# -----------------------------------------------------------------------------
if menu == "👥 Gestão de Colaboradores":
  if df_colab.empty:
    st.warning(
        "Nenhum colaborador encontrado. Execute a migração para popular os"
        " dados."
    )
  else:
    # Seleção de Colaborador
    opcoes_colab = {
        row["id"]: f"{row['nome']} - {row['cargo']}"
        for _, row in df_colab.iterrows()
    }
    colab_id_sel = st.selectbox(
        "Selecione o Colaborador:",
        options=list(opcoes_colab.keys()),
        format_func=lambda x: opcoes_colab[x],
    )

    colab_dados = df_colab[df_colab["id"] == colab_id_sel].iloc[0]

    # Exibição do Perfil
    st.markdown(f"## 👤 {colab_dados['nome']}")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"**💼 Cargo:** {colab_dados.get('cargo') or 'Não informado'}")
    c2.markdown(f"**🏢 Setor:** {colab_dados.get('departamento') or 'MAQ'}")
    c3.markdown(
        f"**👤 Gestor:** {colab_dados.get('gestor') or 'Não informado'}"
    )

    st.markdown("---")
    st.subheader("📋 Gestão Individual por Treinamento (Supabase Cloud Sync)")

    if df_treino.empty:
      st.info("Nenhum treinamento cadastrado no catálogo.")
    else:
      for _, t_row in df_treino.iterrows():
        t_id = t_row["id"]
        t_nome = t_row["nome_curso"]
        t_ch = t_row.get("carga_horaria", 0)

        # Busca registro existente do colaborador para o treinamento específico
        reg_atual = df_reg[
            (df_reg["colaborador_id"] == colab_id_sel)
            & (df_reg["treinamento_id"] == t_id)
        ]

        status_val = "Pendente"
        data_val = None
        inst_nome_val = ""
        inst_cargo_val = ""

        if not reg_atual.empty:
          r_data = reg_atual.iloc[0]
          status_val = r_data.get("status_planilha") or "Pendente"
          inst_nome_val = limpar_valor(r_data.get("instrutor_nome")) or ""
          inst_cargo_val = limpar_valor(r_data.get("aplicador_cargo")) or ""

          data_str = r_data.get("data_realizacao")
          if data_str:
            try:
              data_val = datetime.strptime(
                  str(data_str).split("T")[0], "%Y-%m-%d"
              )
            except Exception:
              data_val = None

        with st.expander(
            f"📌 {t_nome} ({t_ch}h)", expanded=(status_val == "Concluído")
        ):
          col_a, col_b, col_c, col_d = st.columns([2, 2, 2, 2])

          with col_a:
            novo_status = st.selectbox(
                "Status",
                ["Pendente", "Em Andamento", "Concluído"],
                index=[
                    "Pendente",
                    "Em Andamento",
                    "Concluído",
                ].index(
                    status_val if status_val in ["Pendente", "Em Andamento", "Concluído"] else "Pendente"
                ),
                key=f"status_{colab_id_sel}_{t_id}",
            )

          with col_b:
            nova_data = st.date_input(
                "Data Realização",
                value=data_val if data_val else datetime.now(),
                key=f"data_{colab_id_sel}_{t_id}",
            )

          with col_c:
            novo_inst_nome = st.text_input(
                "Nome Aplicador",
                value=inst_nome_val,
                key=f"inst_nome_{colab_id_sel}_{t_id}",
            )

          with col_d:
            novo_inst_cargo = st.text_input(
                "Cargo Aplicador",
                value=inst_cargo_val,
                key=f"inst_cargo_{colab_id_sel}_{t_id}",
            )

          # BOTÃO DE SALVAMENTO COM UPSERT TRATADO
          if st.button(
              f"💾 Salvar Atualização de '{t_nome}'",
              key=f"btn_{colab_id_sel}_{t_id}",
          ):
            try:
              payload = {
                  "colaborador_id": int(colab_id_sel),
                  "treinamento_id": int(t_id),
                  "status_planilha": novo_status,
                  "data_realizacao": (
                      nova_data.strftime("%Y-%m-%d") if nova_data else None
                  ),
                  "instrutor_nome": limpar_valor(novo_inst_nome),
                  "aplicador_cargo": limpar_valor(novo_inst_cargo),
              }

              # Executa Upsert de forma limpa sem disparar APIError
              supabase.table("registros").upsert(
                  payload, on_conflict="colaborador_id,treinamento_id"
              ).execute()

              st.cache_data.clear()
              st.success(f"✅ Alteração em '{t_nome}' salva com sucesso!")
              st.rerun()
            except Exception as e:
              # Fallback de gravação caso a constraint de conflito não esteja mapeada
              try:
                supabase.table("registros").upsert(payload).execute()
                st.cache_data.clear()
                st.success(f"✅ Registrado com sucesso!")
                st.rerun()
              except Exception as ex:
                st.error(f"Erro ao salvar registro: {ex}")

# -----------------------------------------------------------------------------
# MODULO 2: DASHBOARD EXECUTIVO
# -----------------------------------------------------------------------------
elif menu == "📊 Dashboard Executivo":
  st.subheader("📊 Indicadores Gerais do Sistema")

  c1, c2, c3 = st.columns(3)
  c1.metric("Total de Colaboradores", len(df_colab))
  c2.metric("Total de Treinamentos", len(df_treino))

  concluidos = (
      len(df_reg[df_reg["status_planilha"] == "Concluído"])
      if not df_reg.empty
      else 0
  )
  c3.metric("Treinamentos Concluídos", concluidos)

  st.markdown("---")
  st.dataframe(df_colab, use_container_width=True)

# -----------------------------------------------------------------------------
# MODULO 3: CATÁLOGO DE TREINAMENTOS
# -----------------------------------------------------------------------------
elif menu == "📚 Catálogo de Treinamentos":
  st.subheader("📚 Cursos e Treinamentos Cadastrados")
  st.dataframe(df_treino, use_container_width=True)
