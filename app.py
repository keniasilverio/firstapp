import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime
import time

st.set_page_config(layout="wide")
st.title("🌻 Helianthus - Painel ENTSO-E (28/04/2025)")

st.markdown(
    """
    Bem-vindo ao painel de energia da **Helianthus**.  
    Aqui você pode visualizar os dados públicos da ENTSO-E para Portugal, Espanha, França e Alemanha no dia **28 de abril de 2025**:

    - 🔆 Geração por tipo (fonte)
    - 🔋 Carga elétrica total (load)
    - 💶 Preço spot (day-ahead)

    > Desenvolvido por **Kenia Silverio**  
    👉 [LinkedIn](https://www.linkedin.com/in/kenia-silv%C3%A9rio-2b391bb7/)
    """
)

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

def consulta_load(client, nome, code):
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

def consulta_preco(client, nome, code):
    try:
        with st.spinner(f"💶 Preço de {nome}..."):
            return tentar_n_vezes(lambda: (
                client.query_day_ahead_prices(code, start=start, end=end)
                .reset_index()
                .rename(columns={0: "Preço (€/MWh)"})
                .assign(País=nome)
            ))
    except Exception as e:
        st.warning(f"⚠️ Preço - {nome}: {e}")
        return pd.DataFrame()

# --- Botão de carregamento
if api_key:
    if st.button("🔁 Carregar dados de geração, carga e preço"):
        client = EntsoePandasClient(api_key=api_key)

        st.subheader("🔄 Carregando dados da ENTSO-E...")
        geracoes, cargas, precos = [], [], []

        for nome, code in paises.items():
            geracoes.append(consulta_geracao(client, nome, code))
            cargas.append(consulta_load(client, nome, code))
            precos.append(consulta_preco(client, nome, code))

        # --- Visualização em abas
        tab1, tab2, tab3 = st.tabs(["🔆 Geração", "🔋 Carga", "💶 Preço"])

        with tab1:
            st.subheader("🔆 Geração por tipo e país")
            df_g = pd.concat(geracoes)
            if not df_g.empty:
                pais_sel = st.selectbox("Escolha o país", df_g["País"].unique().tolist())
                graf = df_g[df_g["País"] == pais_sel]
                fig = px.area(graf, x="Data", y="MW", color="Fonte", title=f"Geração - {pais_sel}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Nenhum dado de geração retornado.")

        with tab2:
            st.subheader("🔋 Carga por país")
            df_l = pd.concat(cargas)
            if not df_l.empty:
                fig2 = px.line(df_l, x="Data", y="MW", color="País", title="Carga total", markers=True)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("Nenhum dado de carga retornado.")

        with tab3:
            st.subheader("💶 Preço spot por país")
            df_p = pd.concat(precos)
            if not df_p.empty:
                fig3 = px.line(df_p, x=df_p.columns[0], y="Preço (€/MWh)", color="País", title="Preço Spot", markers=True)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("Nenhum dado de preço retornado.")
else:
    st.info("Insira seu token para carregar os dados da ENTSO-E.")
