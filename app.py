import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta
import pytz
import time
import streamlit.components.v1 as components
import os
import requests

st.set_page_config(layout="wide")
st.title("🌻 Helianthus – ENTSO-E + Solar Insights")

# Sidebar menu
sections = ["📊 Dashboard", "🔆 Generation", "🔋 Load", "💶 Day-Ahead Prices", "ℹ️ EEG Info", "🌞 PVGIS Solar"]
selected_section = st.sidebar.selectbox("🔍 Select section", sections)

api_key = st.sidebar.text_input("🔐 ENTSO-E token", type="password")
today = datetime.now()
default_start = today - timedelta(days=7)
start_date, end_date = st.sidebar.date_input("📅 Date range", value=(default_start, today), max_value=today)

country_codes = {
    "Portugal": "PT",
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Belgium": "BE",
    "Netherlands": "NL"
}
selected_countries = st.sidebar.multiselect("🌍 Countries", list(country_codes.keys()), default=["Germany", "Portugal", "Spain"])

start = pd.Timestamp(start_date, tz="Europe/Brussels")
end = pd.Timestamp(end_date + timedelta(days=1), tz="Europe/Brussels")

def try_multiple_times(function, attempts=2, wait=2):
    for i in range(attempts):
        try:
            return function()
        except Exception as e:
            if i < attempts - 1:
                time.sleep(wait)
            else:
                raise e

def fetch_generation(client, name, code):
    try:
        with st.spinner(f"⚡ Fetching generation for {name}..."):
            def query():
                gen = client.query_generation(code, start=start, end=end, psr_type=None)
                if isinstance(gen.columns, pd.MultiIndex):
                    gen.columns = gen.columns.get_level_values(0)
                df = gen.reset_index()
                df_melted = df.melt(id_vars=df.columns[0], var_name="Source", value_name="MW")
                df_melted.columns = ["Datetime", "Source", "MW"]
                df_melted["Country"] = name
                return df_melted
            return try_multiple_times(query)
    except Exception as e:
        st.warning(f"⚠️ Generation – {name}: {e}")
        return pd.DataFrame()

def fetch_load(client, name, code):
    try:
        with st.spinner(f"🔋 Fetching load for {name}..."):
            def query():
                load = client.query_load(code, start=start, end=end)
                df = pd.DataFrame()
                df["Datetime"] = load.index
                df["MW"] = list(load.values)
                df["Country"] = name
                return df
            return try_multiple_times(query)
    except Exception as e:
        st.warning(f"⚠️ Load – {name}: {e}")
        return pd.DataFrame()

def fetch_price(client, name, code):
    try:
        with st.spinner(f"💶 Fetching prices for {name}..."):
            return try_multiple_times(lambda: (
                client.query_day_ahead_prices(code, start=start, end=end)
                .reset_index()
                .rename(columns={0: "Price (€/MWh)"})
                .assign(Country=name)
            ))
    except Exception as e:
        st.warning(f"⚠️ Price – {name}: {e}")
        return pd.DataFrame()

if selected_section == "📊 Dashboard":
    st.markdown(
        '''
        Welcome to the **Helianthus Energy Dashboard**.  
        Explore real-time data and solar potential across Europe.

        - 🔆 Generation mix  
        - 🔋 Electricity load  
        - 💶 Day-ahead prices  
        - 🌞 Monthly irradiation potential  
        - ℹ️ EEG (FIT) incentives for rooftop solar  

        > Created by **Kenia Silverio**  
        👉 [LinkedIn](https://www.linkedin.com/in/kenia-silverio/)
        '''
    )

elif selected_section == "🌞 PVGIS Solar":
    st.subheader("🌞 Monthly Solar Irradiation – Germany")
    st.markdown("This map shows average monthly solar irradiation (kWh/m²) for several German cities.")

    file_path = "solar_irradiation_map_germany.html"
    file_url = "https://raw.githubusercontent.com/openai-sandbox-kenia/data/main/solar_irradiation_map_germany.html"

    if not os.path.exists(file_path):
        st.info("Downloading solar irradiation map...")
        try:
            response = requests.get(file_url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                st.success("Map downloaded successfully!")
            else:
                st.error("Failed to download map file.")
        except Exception as e:
            st.error(f"Download error: {e}")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            components.html(html_content, height=600, scrolling=True)

    st.markdown("Data source: [PVGIS – European Commission](https://re.jrc.ec.europa.eu/pvg_tools/en/)")
