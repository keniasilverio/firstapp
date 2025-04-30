import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime
import pytz

st.set_page_config(layout="wide")
st.title("⚡️ Dados ENTSO-E - 28 de Abril de 2025 (Helianthus 🌻)")

# Token
api_key = st.text_input("🔐 Cole seu token ENTSO-E aqui:", type="password")

# Datas com timezone Europe/Brussels (usada pela ENTSO-E)
start = pd.Timestamp("2025-04-28 00:00:00", tz="Europe/Brussels")
end = pd.Timestamp("2025-04-29 00:00:00", tz="Europe/Brussels")

@st.cache_data(show_spinner=True)
def carregar_dados(api_key):
    client = EntsoePandasClient(api_key=api_key)
    paises = {
        "Portugal": "PT",
        "Espanha": "ES",
        "França": "FR",
        "Alemanha": "DE"
    }

    cargas, geracoes, precos, fluxos = [], [], [], []

    for nome, code in paises.items():
        # --- Carga
        try:
            carga = client.query_load(code, start=start, end=end)
            df_carga = carga.reset_index()
            df_carga.columns = ["Data", "MW"]
            df_carga["País"] = nome
            cargas.append(df_carga)
        except Exception as e:
            st.warning(f"⚠️ Falha ao carregar carga de {nome}: {e}")

        # --- Geração
        try:
            gen = client.query_generation(code, start=start, end=end, psr_type=None)
            # Se MultiIndex nas colunas, remover
            if isinstance(gen.columns, pd.MultiIndex):
                gen.columns = gen.columns.get_level_values(0)
            df_gen = gen.reset_index().melt(id_vars="datetime", var_name="Tipo", value_name="MW")
            df_gen.columns = ["Data", "Fonte", "MW"]
            df_gen["País"] = nome
            geracoes.append(df_gen)
        except Exception as e:
            st.warning(f"⚠️ Falha ao carregar geração de {nome}: {e}")

        # --- Preço spot
        try:
            preco = client.query_day_ahead_prices(code, start=start, end=end)
            df_preco = preco.reset_index()
            df_preco.columns = ["Data", "Preço (€/MWh)"]
            df_preco["País"] = nome
            precos.append(df_preco)
        except Exception as e:
            st.warning(f"⚠️ Falha ao carregar preço de {nome}: {e}")

    # --- Fluxo PT ↔ ES
    try:
        fluxo1 = client.query_crossborder_flows("PT", "ES", start=start, end=end)
        df_fluxo1 = fluxo1.reset_index()
        df_fluxo1.columns = ["Data", "Fluxo (MW)"]
        df_fluxo1["Direção"] = "PT → ES"

        fluxo2 = client.query_crossborder_flows("ES", "PT", start=start, end=end)
        df_fluxo2 = fluxo2.reset_index()
        df_fluxo2.columns = ["Data", "Fluxo (MW)"]
        df_fluxo2["Direção"] = "ES → PT"

        fluxos.extend([df_fluxo1, df_fluxo2])
    except Exception as e:
        st.warning(f"⚠️ Falha nos fluxos PT↔ES: {e}")

    return (
        pd.concat(cargas) if cargas else pd.DataFrame(),
        pd.concat(geracoes) if geracoes else pd.DataFrame(),
        pd.concat(precos) if precos else pd.DataFrame(),
        pd.concat(fluxos) if fluxos else pd.DataFrame()
    )

# EXECUÇÃO
if api_key:
    carga_df, geracao_df, preco_df, fluxo_df = carregar_dados(api_key)

    tab1, tab2, tab3, tab4 = st.tabs(["📉 Carga", "🔆 Geração", "💶 Preço Spot", "🔁 Fluxo PT ↔ ES"])

    with tab1:
        st.subheader("📉 Carga por país")
        if carga_df.empty:
            st.warning("Nenhum dado de carga retornado.")
        else:
            st.dataframe(carga_df.head())
            fig1 = px.line(carga_df, x="Data", y="MW", color="País", title="Carga elétrica - 28/04/2025", markers=True)
            st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.subheader("🔆 Geração por tipo e país")
        if geracao_df.empty:
            st.warning("Nenhum dado de geração retornado.")
        else:
            st.dataframe(geracao_df.head())
            paises = geracao_df["País"].unique().tolist()
            pais_sel = st.selectbox("Escolha o país", paises)
            df_g = geracao_df[geracao_df["País"] == pais_sel]
            fig2 = px.area(df_g, x="Data", y="MW", color="Fonte", title=f"Geração por tipo - {pais_sel}")
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("💶 Preço Day-Ahead")
        if preco_df.empty:
            st.warning("Nenhum dado de preço retornado.")
        else:
            st.dataframe(preco_df.head())
            fig3 = px.line(preco_df, x="Data", y="Preço (€/MWh)", color="País", title="Preço Spot - 28/04/2025", markers=True)
            st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        st.subheader("🔁 Fluxo de energia - PT ↔ ES")
        if fluxo_df.empty:
            st.warning("Nenhum dado de fluxo retornado.")
        else:
            st.dataframe(fluxo_df.head())
            fig4 = px.line(fluxo_df, x="Data", y="Fluxo (MW)", color="Direção", title="Importação/Exportação PT ↔ ES")
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("Cole seu token ENTSO-E acima para visualizar os dados.")
