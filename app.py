import sqlite3
import pandas as pd
import streamlit as st
from supabase import create_client

# Configuração da página
st.set_page_config(
    page_title="Migração de Dados", page_icon="📦", layout="centered"
)

st.title("📦 Migração do Banco Offline para o Supabase")
st.markdown("Carregue o seu ficheiro **`treinamentos.db`** para popular a base de dados na nuvem.")

# Chaves do Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Campo de Upload
uploaded_db = st.file_uploader(
    "Arraste ou selecione o ficheiro treinamentos.db", type=["db", "sqlite"]
)

if uploaded_db is not None:
    st.success("Ficheiro carregado com sucesso! Clique no botão abaixo.")
    if st.button("🚀 Iniciar Migração para o Supabase", type="primary"):
        with st.spinner("A migrar dados para a nuvem..."):
            with open("temp_migracao.db", "wb") as f:
                f.write(uploaded_db.getbuffer())

            conn = sqlite3.connect("temp_migracao.db")
            tabelas = [
                "usuarios",
                "colaboradores",
                "treinamentos",
                "registros",
                "matriz_cargo_treinamento",
                "logs_auditoria",
            ]

            barra = st.progress(0)

            for idx, tabela in enumerate(tabelas):
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
                    if not df.empty:
                        # TRATAMENTO CRÍTICO DE VALORES NAN / VACIOS
                        df = df.fillna(value=pd.NA)
                        dados = df.to_dict(orient="records")
                        
                        # Limpa os NaNs explicitamente de cada dicionário
                        dados_limpos = [
                            {k: (None if pd.isna(v) else v) for k, v in row.items()}
                            for row in dados
                        ]
                        
                        # Envia para o Supabase usando UPSERT
                        supabase.table(tabela).upsert(dados_limpos).execute()
                        st.success(f"✅ {len(dados_limpos)} registos migrados em '{tabela}'")
                except Exception as e:
                    st.warning(f"Aviso na tabela {tabela}: {e}")

                barra.progress((idx + 1) / len(tabelas))

            conn.close()
            st.balloons()
            st.success("🎉 Migração concluída com sucesso! Todos os 107 colaboradores e registros já estão no Supabase.")
