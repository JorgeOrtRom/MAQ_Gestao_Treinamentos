from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS CUSTOMIZADOS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MAQ_Gestao_Treinamentos",
    page_icon="📚",
    layout="wide",
)

# Secrets do Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def limpar_campo(valor):
  """Converte textos 'nan', vazios ou Nulos para None (compatível com JSON do Supabase)."""
  if pd.isna(valor) or str(valor).strip().lower() in ["nan", "none", "null", ""]:
    return None
  return str(valor).strip()


# -----------------------------------------------------------------------------
# 2. CARREGAMENTO DE DADOS COM CACHE
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def buscar_colaboradores():
  res = (
      supabase.table("colaboradores")
      .select("*")
      .order("nome", desc=False)
      .execute()
  )
  df = pd.DataFrame(res.data)
  return df.where(pd.notnull(df), None) if not df.empty else df


@st.cache_data(ttl=5)
def buscar_treinamentos():
  res = (
      supabase.table("treinamentos")
      .select("*")
      .order("nome_curso", desc=False)
      .execute()
  )
  df = pd.DataFrame(res.data)
  return df.where(pd.notnull(df), None) if not df.empty else df


@st.cache_data(ttl=5)
def buscar_registros():
  res = supabase.table("registros").select("*").execute()
  df = pd.DataFrame(res.data)
  return df.where(pd.notnull(df), None) if not df.empty else df


df_colab = buscar_colaboradores()
df_treino = buscar_treinamentos()
df_reg = buscar_registros()

# -----------------------------------------------------------------------------
# 3. CABEÇALHO E NAVEGAÇÃO
# -----------------------------------------------------------------------------
st.sidebar.title("📌 Menu de Navegação")
menu = st.sidebar.radio(
    "Selecione o módulo:",
    [
        "👥 Gestão do Colaborador",
        "📊 Dashboard Executivo",
        "📚 Catálogo de Treinamentos",
    ],
)

# -----------------------------------------------------------------------------
# MÓDULO: GESTÃO DO COLABORADOR (DESIGN ORIGINAL)
# -----------------------------------------------------------------------------
if menu == "👥 Gestão do Colaborador":
  if df_colab.empty:
    st.info("Nenhum colaborador encontrado na base de dados.")
  else:
    colab_dict = {
        row["id"]: f"{row['nome']}"
        for _, row in df_colab.iterrows()
        if row.get("nome")
    }

    colab_id_sel = st.selectbox(
        "Pesquisar Colaborador:",
        options=list(colab_dict.keys()),
        format_func=lambda x: colab_dict[x],
    )

    c_info = df_colab[df_colab["id"] == colab_id_sel].iloc[0]

    # Card do Perfil do Colaborador (Design das Imagens)
    st.markdown(f"## 👤 {c_info['nome'].upper()}")

    meta_cols = st.columns([2.5, 2.5, 2.5, 3.5])
    meta_cols[0].markdown(
        f"💼 **Cargo:** {c_info.get('cargo') or 'Não informado'}"
    )
    meta_cols[1].markdown(
        f"👔 **Gestor:** {c_info.get('gestor') or 'Não informado'}"
    )
    meta_cols[2].markdown(
        f"🏢 **Departamento:** {c_info.get('departamento') or 'Não informado'}"
    )
    meta_cols[3].markdown(
        f"✉️ **E-mail:** {c_info.get('email') or 'Não informado'}"
    )

    st.markdown("---")
    st.subheader("📋 Gestão Individual por Treinamento (Supabase Cloud Sync)")

    if df_treino.empty:
      st.warning("Nenhum treinamento cadastrado no sistema.")
    else:
      for _, t_row in df_treino.iterrows():
        t_id = t_row["id"]
        t_nome = t_row["nome_curso"]

        # Busca registro existente do colaborador
        reg_match = df_reg[
            (df_reg["colaborador_id"] == colab_id_sel)
            & (df_reg["treinamento_id"] == t_id)
        ]

        status_atual = "Pendente"
        data_atual = None
        aplicador_nome = ""
        aplicador_cargo = ""

        if not reg_match.empty:
          r = reg_match.iloc[0]
          status_atual = r.get("status_planilha") or "Pendente"
          aplicador_nome = limpar_campo(r.get("instrutor_nome")) or ""
          aplicador_cargo = limpar_campo(r.get("aplicador_cargo")) or ""

          d_str = r.get("data_realizacao")
          if d_str and str(d_str).strip().lower() != "nan":
            try:
              data_atual = datetime.strptime(
                  str(d_str).split("T")[0], "%Y-%m-%d"
              )
            except Exception:
              data_atual = None

        st.markdown(f"### 🎏 {t_nome}")

        # Grid Horizontal idêntico à imagem enviada
        f1, f2, f3, f4, f5, f6 = st.columns([1.5, 1.5, 2, 2, 2, 1.5])

        with f1:
          status_opcoes = ["Pendente", "Em Andamento", "Concluído"]
          idx_st = (
              status_opcoes.index(status_atual)
              if status_atual in status_opcoes
              else 0
          )
          novo_status = st.selectbox(
              "Status",
              status_opcoes,
              index=idx_st,
              key=f"st_{colab_id_sel}_{t_id}",
          )

        with f2:
          nova_data = st.date_input(
              "Data Aplicação",
              value=data_atual if data_atual else datetime.now(),
              key=f"dt_{colab_id_sel}_{t_id}",
          )

        with f3:
          novo_aplicador = st.text_input(
              "Nome Aplicador",
              value=aplicador_nome,
              key=f"ap_n_{colab_id_sel}_{t_id}",
          )

        with f4:
          novo_cargo_ap = st.text_input(
              "Cargo Aplicador",
              value=aplicador_cargo,
              key=f"ap_c_{colab_id_sel}_{t_id}",
          )

        with f5:
          st.file_uploader(
              "📎 Anexar Forms/Lista",
              type=["pdf", "png", "jpg"],
              key=f"file_{colab_id_sel}_{t_id}",
          )

        with f6:
          st.write("📄 **Ações / Download:**")

        # Botão de Salvamento (Corrigido para evitar o erro postgrest.exceptions.APIError)
        if st.button(
            f"💾 Salvar Atualização de '{t_nome}'",
            key=f"btn_save_{colab_id_sel}_{t_id}",
        ):
          try:
            payload = {
                "colaborador_id": int(colab_id_sel),
                "treinamento_id": int(t_id),
                "status_planilha": novo_status,
                "data_realizacao": (
                    nova_data.strftime("%Y-%m-%d") if nova_data else None
                ),
                "instrutor_nome": limpar_campo(novo_aplicador),
                "aplicador_cargo": limpar_campo(novo_cargo_ap),
            }

            # Atualiza ou Insere sem violar constraints nem gerar NaN no JSON
            supabase.table("registros").upsert(payload).execute()

            st.cache_data.clear()
            st.success(f"✅ Atualização salva com sucesso!")
            st.rerun()

          except Exception as ex:
            st.error(f"Erro ao atualizar registro no Supabase: {ex}")

        st.markdown("---")

# -----------------------------------------------------------------------------
# MÓDULO: DASHBOARD EXECUTIVO
# -----------------------------------------------------------------------------
elif menu == "📊 Dashboard Executivo":
  st.subheader("📊 Visão Geral da Matriz de Treinamentos")
  m1, m2, m3 = st.columns(3)
  m1.metric("Colaboradores Ativos", len(df_colab))
  m2.metric("Treinamentos no Catálogo", len(df_treino))

  qtd_concluidos = (
      len(df_reg[df_reg["status_planilha"] == "Concluído"])
      if not df_reg.empty
      else 0
  )
  m3.metric("Treinamentos Concluídos", qtd_concluidos)

  st.markdown("---")
  st.dataframe(df_colab, use_container_width=True)

# -----------------------------------------------------------------------------
# MÓDULO: CATÁLOGO DE TREINAMENTOS
# -----------------------------------------------------------------------------
elif menu == "📚 Catálogo de Treinamentos":
  st.subheader("📚 Cursos e Exigências Cadastradas")
  st.dataframe(df_treino, use_container_width=True)
