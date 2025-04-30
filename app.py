import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

st.title("App Helianthus com dados da ENTSO-E 🌻")

token = st.text_input("Insira seu token da ENTSO-E:", type="password")

if token:
    st.write("🔄 Buscando dados de geração na Alemanha...")

    # Datas: últimos 2 dias
    now = datetime.utcnow()
    start = (now - timedelta(days=2)).strftime("%Y%m%d%H%M")
    end = now.strftime("%Y%m%d%H%M")

    # Parâmetros da ENTSO-E API
    params = {
        "documentType": "A75",  # geração por tipo
        "processType": "A16",   # valores reais
        "outBiddingZone_Domain": "10Y1001A1001A83F",  # Alemanha
        "periodStart": start,
        "periodEnd": end,
        "securityToken": token
    }

    url = "https://web-api.transparency.entsoe.eu/api"

    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            rows = []
            for timeseries in root.findall(".//{*}TimeSeries"):
                prod_type = timeseries.findtext(".//{*}psrType")
                for point in timeseries.findall(".//{*}Point"):
                    position = point.findtext("{*}position")
                    quantity = point.findtext("{*}quantity")
                    rows.append((prod_type, position, quantity))
            df = pd.DataFrame(rows, columns=["Tipo", "Posição", "Quantidade"])
            st.dataframe(df.head(20))
        else:
            st.error("Erro ao buscar dados da ENTSO-E. Verifique seu token.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

