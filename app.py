import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("⚡️ Painel Energético Europeu - Dados Locais (Helianthus 🌻)")

tab1, tab2, tab3 = st.tabs(["🔆 Geração", "📉 Carga (Load)", "🔀 Fluxo PT ↔ ES"])

# --- Aba 1: Geração
with tab1:
    st.header("🔆 Geração por tipo - Europa")
    try:
        df_geracao = pd.read_excel("generation_2025-04-28_cleaned.xlsx")
        data_disponivel = df_geracao["Data"].unique()
        st.info(f"📅 Dados referentes ao dia: {data_disponivel[0]}")
        pais = st.selectbox("Selecione o país:", df_geracao["País"].unique())
        df_p = df_geracao[df_geracao["País"] == pais]

        st.dataframe(df_p.head())

        fig = px.bar(
            df_p,
            x="Data",
            y="Quantidade (MWh)",
            color="Tipo",
            barmode="stack",
            title=f"Geração por tipo em {pais}"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados de geração: {e}")

# --- Aba 2: Carga
with tab2:
    st.header("📉 Carga por país - Blackout 2025")
    try:
        df_carga = pd.read_excel("carga_blackout_2025_dados.xlsx")
        st.info(f"📅 Período disponível: de {df_carga['Data'].min()} até {df_carga['Data'].max()}")
        pais_c = st.selectbox("Selecione o país:", df_carga["País"].unique())
        df_c = df_carga[df_carga["País"] == pais_c]

        st.dataframe(df_c.head())

        fig_c = px.line(
            df_c,
            x="Data",
            y="Carga (MW)",
            title=f"Carga elétrica em {pais_c} - 2025",
            markers=True
        )
        st.plotly_chart(fig_c, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados de carga: {e}")

# --- Aba 3: Fluxo PT ↔ ES
with tab3:
    st.header("🔀 Fluxo transfronteiriço: Portugal ↔ Espanha")
    try:
        df1 = pd.read_excel("crossborder_detailed_PT_ES_2025-04-27.xlsx")
        df2 = pd.read_excel("crossborder_flows_PT_ES_2025-04-28.xlsx")
        df_fluxo = pd.concat([df1, df2])
        st.info(f"📅 Período analisado: de {df_fluxo['Data'].min()} até {df_fluxo['Data'].max()}")

        st.dataframe(df_fluxo.head())

        fig_f = px.line(
            df_fluxo,
            x="Data",
            y="Quantidade (MWh)",
            color="Direção",
            title="Importação e Exportação PT ↔ ES (27-28/04/2025)",
            markers=True
        )
        st.plotly_chart(fig_f, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados de fluxo: {e}")
