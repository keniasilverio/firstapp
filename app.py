import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("⚡️ Painel Energético Europeu - Dados Locais (Helianthus 🌻)")

# === TABS ===
tab0, tab1, tab2, tab3 = st.tabs([
    "📘 Sobre o projeto",
    "🔆 Geração",
    "📉 Carga (Load)",
    "🔀 Fluxo PT ↔ ES"
])

# --- Aba 0: Sobre o Projeto
with tab0:
    st.header("📘 Bem-vindo ao Painel Helianthus")
    st.markdown("""
    Este painel apresenta dados energéticos reais ou simulados da Europa, com foco em:

    - Geração elétrica por tipo
    - Carga total dos sistemas (Load)
    - Fluxos transfronteiriços (ex: Portugal ↔ Espanha)

    Os dados são atualizados manualmente a partir de arquivos locais, até que a integração com a API da ENTSO-E esteja completa.

    **Desenvolvido por:** Helianthus ☀️  
    **Contato:** [linkedin.com/in/kenia-silverio](https://www.linkedin.com/in/kenia-silverio)
    """)

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

        st.markdown("💡 **Observação**: Geração com predominância de fontes renováveis indica boa performance ambiental.")
    except Exception as e:
        st.error(f"Erro ao carregar dados de geração: {e}")

# --- Aba 2: Carga
with tab2:
    st.header("📉 Carga - Blackout 2025")
    try:
        df_carga = pd.read_excel("carga_blackout_2025_dados.xlsx")
        df_carga = df_carga.rename(columns={"TIME": "Data", "Actual Load": "Carga (MW)"})

        st.info(f"📅 Período disponível: de {df_carga['Data'].min()} até {df_carga['Data'].max()}")

        st.dataframe(df_carga.head())

        fig_c = px.line(
            df_carga,
            x="Data",
            y="Carga (MW)",
            title="Carga elétrica durante o blackout de 2025",
            markers=True
        )
        st.plotly_chart(fig_c, use_container_width=True)

        st.markdown("⚠️ **Insight**: Observe os picos e quedas bruscas de carga — podem indicar instabilidade.")
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

        st.markdown("🌍 **Nota**: Fluxos equilibrados entre os países são sinais de estabilidade e boa interconexão.")
    except Exception as e:
        st.error(f"Erro ao carregar dados de fluxo: {e}")
