import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime
import time

st.set_page_config(layout="wide")
st.title("⚡️ Dados ENTSO-E - 28 de Abril de 2025 (Helianthus 🌻)")

api_key = st.text_input("🔐 Cole seu token ENTSO-E aqui:", type="password")

start = pd.Timestamp("2025-04-28 00:00:00", tz="Europe/Brussels")
end = pd.Timestamp("2025-04-29 00:00:00", tz="Europe/Brussels")

paises = {
    "Portugal": "PT",
    "Espanha": "ES",
    "França": "FR",
    "Alemanha": "DE"
}

def tentar_n_vezes(funcao, tentativas=2, espera=2):
    for i in range(tentativas):
        try:
            return funcao()
        except Exception as e:
            if i < tentativas - 1:
                time.sleep(espera)
            else:
                raise e

@st.cache_data(show_spinner=False)
def consulta_carga(client, nome, code):
    try:
        with st.spinner(f"🔋 Carga de {nome}..."):
            return tentar_n_vezes(lambda: (
                pd.DataFrame({
                    "Data": client.query_load(code, start=start, end=end).index,
                    "MW": client.query_load(code, start=start, end=end).values,
                    "País": nome
                })
            ))
    except Exception as e:
        st.warning(f"⚠️ Carga - {nome}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def consulta_geracao(client, nome, code):
    try:
        with st.spinner(f"⚡ Geração de {nome}..."):
            def consulta():
                gen = client.query_generation(code, start=start, end=end, psr_type=None)
                if isinstance(gen.columns, pd.MultiIndex):
                    gen.columns = gen.columns.get_level_values(0)
                df = gen.reset_index()
                index_col = df.columns[0]
                df_melt = df.melt(id_vars=index_col, var_name="Tipo", value_name="MW")
                df_melt.columns = ["Data", "Fonte", "MW"]
                df_melt["País"] = nome
                return df_melt
            return tentar_n_vezes(consulta)
    except Exception as e:
        st.warning(f"⚠️ Geração - {nome}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def consulta_preco(client, nome, code):
    try:
        with st.spinner(f"💶 Preço de {nome}..."):
            return tentar_n_vezes(lambda: (
                client.query_day_ahead_prices(code, start=start, end=end)
                .reset_index()
                .rename(columns={"MTU (CET)": "Data", 0: "Preço (€/MWh)"})
                .assign(País=nome)
            ))
    except Exception as e:
        st.warning(f"⚠️ Preço - {nome}: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def consulta_fluxo(client):
    try:
        with st.spinner("🔁 Fluxos PT ↔ ES..."):
            def consulta():
                f1 = client.query_crossborder_flows("PT", "ES", start=start, end=end)
                f2 = client.query_crossborder_flows("ES", "PT", start=start, end=end)
                df1 = f1.reset_index()
                df1.columns = ["Data", "Fluxo (MW)"]
                df1["Direção"] = "PT → ES"
                df2 = f2.reset_index()
                df2.columns = ["Data", "Fluxo (MW)"]
                df2["Direção"] = "ES → PT"
                return pd.concat([df1, df2])
            return tentar_n_vezes(consulta)
    except Exception as e:
        st.warning(f"⚠️ Fluxo: {e}")
        return pd.DataFrame()

# --- Execução
if api_key:
    if st.button("🔁 Carregar dados"):
        client = EntsoePandasClient(api_key=api_key)

        cargas = pd.concat([consulta_carga(client, n, c) for n, c in paises.items()])
        geracoes = pd.concat([consulta_geracao(client, n, c) for n, c in paises.items()])
        precos = pd.concat([consulta_preco(client, n, c) for n, c in paises.items()])
        fluxos = consulta_fluxo(client)

        tab1, tab2, tab3, tab4 = st.tabs(["📉 Carga", "🔆 Geração", "💶 Preço Spot", "🔁 Fluxo PT ↔ ES"])

        with tab1:
            st.subheader("📉 Carga por país")
            if not cargas.empty:
                st.dataframe(cargas.head())
                fig = px.line(cargas, x="Data", y="MW", color="País", title="Carga elétrica", markers=True)
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("🔆 Geração por tipo e país")
            if not geracoes.empty:
                pais_sel = st.selectbox("Escolha o país", geracoes["País"].unique().tolist())
                df_g = geracoes[geracoes["País"] == pais_sel]
                fig = px.area(df_g, x="Data", y="MW", color="Fonte", title=f"Geração - {pais_sel}")
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("💶 Preço Day-Ahead")
            if not precos.empty:
                fig = px.line(precos, x="Data", y="Preço (€/MWh)", color="País", title="Preço Spot", markers=True)
                st.plotly_chart(fig, use_container_width=True)

        with tab4:
            st.subheader("🔁 Fluxo de energia - PT ↔ ES")
            if not fluxos.empty:
                fig = px.line(fluxos, x="Data", y="Fluxo (MW)", color="Direção", title="Fluxo PT ↔ ES")
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Clique em '🔁 Carregar dados' para iniciar a consulta.")
else:
    st.info("Insira seu token da ENTSO-E para habilitar o botão.")
