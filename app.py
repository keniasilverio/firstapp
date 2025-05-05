import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta
import pytz
import time
import streamlit.components.v1 as components

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

elif selected_section == "🔆 Generation" and api_key:
    client = EntsoePandasClient(api_key=api_key)
    generation_data = [fetch_generation(client, name, country_codes[name]) for name in selected_countries]
    df_gen = pd.concat([df for df in generation_data if not df.empty], ignore_index=True)
    if not df_gen.empty:
        st.subheader("🔆 Generation by source")
        fig = px.area(df_gen, x="Datetime", y="MW", color="Source", facet_col="Country", title="Electricity Generation")
        st.plotly_chart(fig, use_container_width=True)
        csv = df_gen.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Generation CSV", csv, "generation.csv", "text/csv")

elif selected_section == "🔋 Load" and api_key:
    client = EntsoePandasClient(api_key=api_key)
    load_data = [fetch_load(client, name, country_codes[name]) for name in selected_countries]
    valid_loads = [df for df in load_data if not df.empty]
    if valid_loads:
        df_load = pd.concat(valid_loads, ignore_index=True)
        df_load["MW"] = df_load["MW"].apply(lambda x: float(str(x).strip("[]")))
        df_load["Datetime"] = pd.to_datetime(df_load["Datetime"], utc=True)
        st.subheader("🔋 Load by country")
        fig = px.line(df_load, x="Datetime", y="MW", color="Country", title="Total Load", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        csv = df_load.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Load CSV", csv, "load.csv", "text/csv")

elif selected_section == "💶 Day-Ahead Prices" and api_key:
    client = EntsoePandasClient(api_key=api_key)
    price_data = [fetch_price(client, name, country_codes[name]) for name in selected_countries]
    valid_prices = [df for df in price_data if not df.empty]
    if valid_prices:
        df_price = pd.concat(valid_prices, ignore_index=True)
        st.subheader("💶 Spot Market Prices")
        fig = px.line(df_price, x=df_price.columns[0], y="Price (€/MWh)", color="Country", title="Day-Ahead Prices", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        csv = df_price.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Price CSV", csv, "prices.csv", "text/csv")

elif selected_section == "ℹ️ EEG Info":
    st.subheader("ℹ️ Feed-in Tariff – EEG 2025 (Germany)")

    if st.button("📄 Show FIT Table"):
        st.markdown(
            """
            ### ⚡ Feed-in Tariff (EEG) – Germany (Feb to Jul 2025)

            | System Size           | Injection Type         | Tariff (ct/kWh) |
            |-----------------------|------------------------|-----------------|
            | Up to 10 kWp          | Partial (self-consumed)| 7.94            |
            |                       | Total (fully injected) | 12.60           |
            | 10 to 40 kWp          | Partial                | 6.88            |
            |                       | Total                  | 10.56           |
            | 40 to 100 kWp         | Partial                | 5.62            |
            |                       | Total                  | 10.56           |

            **Notes:**
            - "Partial" = self-consumption with excess fed into the grid.
            - "Total" = full injection to the grid.
            - Tariffs are guaranteed for 20 years.
            - Updated every 6 months by BNetzA.
            - Future adjustments may apply (e.g., +1.5 ct/kWh in the "Solarpaket I").

            🔗 [BNetzA – EEG Förderhöhe](https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/ErneuerbareEnergien/EEG_Foerderung/start.html)
            🔗 [EEG Tariff Overview (PDF)](https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/Sachgebiete/Energie/Unternehmen_Institutionen/ErneuerbareEnergien/Photovoltaik/ZubauzahlenPV_EEG/EEG-VergSaetze.pdf)
            """,
            unsafe_allow_html=True
        )

elif selected_section == "🌞 PVGIS Solar":
    st.subheader("🌞 Monthly Solar Irradiation – Germany")
    st.markdown("This map shows average monthly solar irradiation (kWh/m²) for several German cities.")
    with open("solar_irradiation_map_germany.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        components.html(html_content, height=600, scrolling=True)
    st.markdown("Data source: [PVGIS – European Commission](https://re.jrc.ec.europa.eu/pvg_tools/en/)")

else:
    st.info("Enter your ENTSO-E token and select a section to begin.")
