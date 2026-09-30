import streamlit as st
import sqlite3
import pandas as pd
from supabase import create_client

# Configuração de Secrets do Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- BOTÃO DE MIGRAÇÃO TEMPORÁRIO NA BARRA LATERAL ---
st.sidebar.markdown("---")
st.sidebar.subheader("📦 Migração de Dados")
uploaded_db = st.sidebar.file_uploader("Envie o seu ficheiro treinamentos.db", type=["db", "sqlite"])

if uploaded_db is not None:
    if st.sidebar.button("🚀 Iniciar Migração para o Supabase"):
        # Salvar o ficheiro temporariamente
        with open("temp_migracao.db", "wb") as f:
            f.write(uploaded_db.getbuffer())
        
        conn = sqlite3.connect("temp_migracao.db")
        tabelas = ["usuarios", "colaboradores", "treinamentos", "registros", "matriz_cargo_treinamento", "logs_auditoria"]
        
        progresso = st.sidebar.progress(0)
        
        for idx, tabela in enumerate(tabelas):
            try:
                df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
                if not df.empty:
                    # Substituir valores NaNs/Nulos para formato compatível
                    df = df.where(pd.notnull(df), None)
                    dados = df.to_dict(orient="records")
                    
                    # Enviar para o Supabase (Upsert evita duplicados)
                    supabase.table(tabela).upsert(dados).execute()
                    st.sidebar.success(f"✅ {len(dados)} registos migrados em '{tabela}'")
            except Exception as e:
                st.sidebar.warning(f"Aviso na tabela {tabela}: {e}")
            
            progresso.progress((idx + 1) / len(tabelas))
            
        conn.close()
        st.sidebar.balloons()
        st.sidebar.success("🎉 Migração concluída com sucesso! Recarregue a página.")
