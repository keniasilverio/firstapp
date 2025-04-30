import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime
import time

st.set_page_config(layout="wide")
st.title("🌻 Helianthus - Dados de Geração ENTSO-E (28/04/2025)")

st.markdown(
    """
    Bem-vindo ao painel de geração elétrica da **Helianthus**.  
    Aqui você pode visualizar os dados públicos da ENTSO-E para Portugal, Espanha, França e Alemanha no dia **28 de abril de 2025**.

    > Desenvolvido por **Kenia Silverio**  
    👉 [LinkedIn](https://www.linkedin.com/in/kenia-silverio/)
    """
)

# Token do usuário
api_key = st.text_input("🔐 Cole seu token ENTSO-E aqui:", type="password")

# Datas da análise (28/04/2025)
start = pd.Timestamp("2025-04-28 00:00:00", tz="Europe/Brussels")
end = pd.Timestamp("2025-04-29 00:00:00", tz="Europe/Brussels")

# Países a consultar
paises = {
    "Portugal": "PT",
    "Espanha": "ES",
    "França": "FR",
    "Alemanha": "DE"
}

# Função de repetição com espera (para evitar bloqueios)
def tentar_n_vezes(funcao, tentativas=2, espera=2):
    for i in range(tentativas):
        try:
            return funcao()
        except Exception as e:
            if i < tentativas - 1:
                time.sleep(espera)
            else:
                raise e

# Consulta geração por país
def consulta_geracao(client, nome, code):
    try:
        with st.spinner(f"⚡ Carregando geração de {nome}..."):
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
        st.warning(f"⚠️ Erro ao consultar geração de {nome}: {e}")
        return pd.DataFrame()

# Botão para iniciar carregamento
if api_key:
    if st.button("🔁 Carregar dados de geração"):
        client = EntsoePandasClient(api_key=api_key)

        resultados = []
        for nome, code in paises.items():
            df = consulta_geracao(client, nome, code)
            if not df.empty:
                resultados.append(df)

        if resultados:
            geracao_df = pd.concat(resultados)
            st.success("Dados de geração carregados com sucesso!")

            st.subheader("🔆 Geração por tipo e país")
            pais_sel = st.selectbox("Escolha o país", geracao_df["País"].unique().tolist())
            df_pais = geracao_df[geracao_df["País"] == pais_sel]
            fig = px.area(df_pais, x="Data", y="MW", color="Fonte", title=f"Geração elétrica - {pais_sel}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum dado de geração foi retornado.")
else:
    st.info("Insira seu token acima para habilitar o botão.")
