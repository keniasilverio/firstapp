import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="centered")
st.title("⚡️ Análise de Energia na Europa com Helianthus 🌻")
st.write("Explore dados simulados de geração, carga, importação e exportação de energia para Alemanha, França, Portugal e Espanha.")

# Menu principal
opcao = st.radio("O que deseja visualizar?", ["Geração por tipo", "Carga / Importação / Exportação"])

# GERAÇÃO
if opcao == "Geração por tipo":
    @st.cache_data
    def carregar_geracao():
        return pd.read_csv("geracao_europa_completa.csv")

    df = carregar_geracao()
    paises = df["País"].unique().tolist()
    pais_selecionado = st.selectbox("Selecione o país:", paises)

    df_filtrado = df[df["País"] == pais_selecionado]

    st.subheader(f"Tabela de geração - {pais_selecionado}")
    st.dataframe(df_filtrado.head(20))

    st.subheader("📊 Geração por tipo de fonte")
    fig = px.bar(
        df_filtrado,
        x="Data",
        y="Quantidade (MWh)",
        color="Tipo",
        title=f"Geração elétrica em {pais_selecionado}",
        barmode="stack"
    )
    st.plotly_chart(fig, use_container_width=True)

# FLUXO
else:
    @st.cache_data
    def carregar_fluxo():
        return pd.read_csv("fluxo_energia_europa.csv")

    df_fluxo = carregar_fluxo()
    paises_fluxo = df_fluxo["País"].unique().tolist()
    pais_fluxo = st.selectbox("Selecione o país:", paises_fluxo, key="fluxo")

    df_f = df_fluxo[df_fluxo["País"] == pais_fluxo]

    st.subheader(f"Tabela de fluxo energético - {pais_fluxo}")
    st.dataframe(df_f.head(20))

    st.subheader("📊 Carga, importação e exportação")
    fig2 = px.line(
        df_f,
        x="Data",
        y="Quantidade (MWh)",
        color="Métrica",
        markers=True,
        title=f"Fluxo de energia em {pais_fluxo}"
    )
    st.plotly_chart(fig2, use_container_width=True)
