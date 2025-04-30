import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    df_pivot = df_filtrado.pivot_table(index="Data", columns="Tipo", values="Quantidade (MWh)", aggfunc="sum")

    st.subheader(f"Tabela de geração - {pais_selecionado}")
    st.dataframe(df_filtrado.head(20))

    st.subheader("📊 Geração por tipo de fonte")
    fig, ax = plt.subplots(figsize=(10, 5))
    df_pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_ylabel("MWh")
    ax.set_title(f"Geração elétrica em {pais_selecionado}")
    st.pyplot(fig)

# FLUXO
else:
    @st.cache_data
    def carregar_fluxo():
        return pd.read_csv("fluxo_energia_europa.csv")

    df_fluxo = carregar_fluxo()
    paises_fluxo = df_fluxo["País"].unique().tolist()
    pais_fluxo = st.selectbox("Selecione o país:", paises_fluxo, key="fluxo")

    df_f = df_fluxo[df_fluxo["País"] == pais_fluxo]
    df_pivot_fluxo = df_f.pivot_table(index="Data", columns="Métrica", values="Quantidade (MWh)", aggfunc="sum")

    st.subheader(f"Tabela de fluxo energético - {pais_fluxo}")
    st.dataframe(df_f.head(20))

    st.subheader("📊 Carga, importação e exportação")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    df_pivot_fluxo.plot(kind="line", marker='o', ax=ax2)
    ax2.set_ylabel("MWh")
    ax2.set_title(f"Fluxo de energia em {pais_fluxo}")
    st.pyplot(fig2)

