import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("⚡️ Dados ENTSO-E ao vivo - 28 de Abril de 2025 (Helianthus 🌻)")

st.markdown("Este painel consulta diretamente a API da ENTSO-E para exibir dados de carga, geração, importação e exportação para países selecionados em 28/04/2025.")

# Token input
api_key = st.text_input("🔐 Cole aqui seu token da ENTSO-E:", type="password")
data_base = datetime(2025, 4, 28)
start = data_base
end = data_base + timedelta(days=1)

@st.cache_data(show_spinner=True)
def consultar_dados(api_key):
    client = EntsoePandasClient(api_key=api_key)
    paises = {
        "Portugal": "PT",
        "Espanha": "ES",
        "França": "FR",
        "Alemanha": "DE"
    }
    resultados = []

    for nome, code in paises.items():
        try:
            carga = client.query_load(code, start=start, end=end)
            carga = carga.reset_index()
            carga.columns = ["Data", "Carga (MW)"]
            carga["País"] = nome
            resultados.append(carga)
        except Exception as e:
            st.error(f"Erro ao consultar carga de {nome}: {e}")
    
    return pd.concat(resultados)

if api_key:
    try:
        st.subheader("📉 Carga por país")
        df_carga = consultar_dados(api_key)
        st.dataframe(df_carga.head())

        fig = px.line(df_carga, x="Data", y="Carga (MW)", color="País", markers=True,
                      title="Carga elétrica em 28 de Abril de 2025")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro geral ao consultar a ENTSO-E: {e}")
else:
    st.warning("⚠️ Cole seu token acima para carregar os dados ENTSO-E.")
