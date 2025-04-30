import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime
import time

st.set_page_config(layout="wide")
st.title("🌻 Helianthus - Painel ENTSO-E (28/04/2025)")

st.markdown(
    '''
    Bem-vindo ao painel de energia da **Helianthus**.  
    Veja os dados públicos da ENTSO-E para Portugal, Espanha, França e Alemanha no dia **28 de abril de 2025**:

    - 🔆 Geração por tipo (fonte)
    - 🔋 Carga elétrica total (load)
    - 💶 Preço spot (day-ahead)

    > Desenvolvido por **Kenia Silverio**  
    👉 [LinkedIn](https://www.linkedin.com/in/kenia-silv%C3%A9rio-2b391bb7/)
    '''
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
            def consulta():
                carga = client.query_load(code, start=start, end=end)
                df = pd.DataFrame({"Data": carga.index, "MW": carga.values})
                df["País"] = nome
                return df
            return tentar_n_vezes(consulta)
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

# Inicializa cliente se tiver token
if api_key:
    client = EntsoePandasClient(api_key=api_key)

    st.markdown("### 🔘 Selecione a informação que deseja carregar:")

    col1, col2, col3 = st.columns(3)

    if col1.button("🔆 Geração"):
        geracoes = [consulta_geracao(client, n, c) for n, c in paises.items()]
        df_g = pd.concat([df for df in geracoes if not df.empty], ignore_index=True)
        if not df_g.empty:
            st.subheader("🔆 Geração por tipo e país")
            pais_sel = st.selectbox("Escolha o país", df_g["País"].unique().tolist(), key="gen")
            graf = df_g[df_g["País"] == pais_sel]
            fig = px.area(graf, x="Data", y="MW", color="Fonte", title=f"Geração - {pais_sel}")
            st.plotly_chart(fig, use_container_width=True)
            csv = df_g.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar CSV de Geração", csv, "geracao.csv", "text/csv")
        else:
            st.warning("Nenhum dado de geração retornado.")

    if col2.button("🔋 Carga"):
        cargas = [consulta_load(client, n, c) for n, c in paises.items()]
        df_l = pd.concat([df for df in cargas if not df.empty], ignore_index=True)
        if not df_l.empty:
            st.subheader("🔋 Carga por país")
            fig2 = px.line(df_l, x="Data", y="MW", color="País", title="Carga total", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
            csv = df_l.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar CSV de Carga", csv, "carga.csv", "text/csv")
        else:
            st.warning("Nenhum dado de carga retornado.")

    if col3.button("💶 Preço Spot"):
        precos = [consulta_preco(client, n, c) for n, c in paises.items()]
        df_p = pd.concat([df for df in precos if not df.empty], ignore_index=True)
        if not df_p.empty:
            st.subheader("💶 Preço Spot por país")
            fig3 = px.line(df_p, x=df_p.columns[0], y="Preço (€/MWh)", color="País", title="Preço Spot", markers=True)
            st.plotly_chart(fig3, use_container_width=True)
            csv = df_p.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar CSV de Preço Spot", csv, "preco_spot.csv", "text/csv")
        else:
            st.warning("Nenhum dado de preço retornado.")
else:
    st.info("Insira seu token da ENTSO-E para ativar os botões.")
