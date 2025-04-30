import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="centered")
st.title("🌍 Análise de Geração Elétrica na Europa")
st.write("Este app mostra a geração elétrica simulada para Alemanha, França, Portugal e Espanha.")

# Carregar dados
@st.cache_data
def carregar_dados():
    return pd.read_csv("geracao_europa_completa.csv")

df = carregar_dados()

# Escolha do país
paises = df["País"].unique().tolist()
pais_selecionado = st.selectbox("Selecione o país:", paises)

df_filtrado = df[df["País"] == pais_selecionado]

# Pivotar os dados para gráfico
df_pivot = df_filtrado.pivot_table(index="Data", columns="Tipo", values="Quantidade (MWh)", aggfunc="sum")

# Mostrar tabela
st.subheader(f"Tabela de geração elétrica - {pais_selecionado}")
st.dataframe(df_filtrado.head(20))

# Gráfico de barras empilhadas
st.subheader("📊 Geração por tipo de fonte")
fig, ax = plt.subplots(figsize=(10, 5))
df_pivot.plot(kind="bar", stacked=True, ax=ax)
ax.set_ylabel("Quantidade (MWh)")
ax.set_xlabel("Data")
ax.set_title(f"Geração Elétrica em {pais_selecionado}")
st.pyplot(fig)


