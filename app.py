import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(layout="wide")
st.title("🌻 Helianthus – ENTSO-E Dashboard")

st.markdown(
    '''
    Welcome to the **Helianthus Energy Dashboard**.  
    Explore ENTSO-E public data for selected European countries:

    - 🔆 Generation by source  
    - 🔋 Total electricity load  
    - 💶 Day-ahead market prices

    > Developed by **Kenia Silverio**  
    👉 [LinkedIn](https://www.linkedin.com/in/kenia-silverio/)
    '''
)

api_key = st.text_input("🔐 Enter your ENTSO-E token:", type="password")

# 📅 Date range input
today = datetime.now()
default_start = today - timedelta(days=7)
start_date, end_date = st.date_input("📅 Select date range", value=(default_start, today), max_value=today)

# Convert to timezone
start = pd.Timestamp(start_date, tz="Europe/Brussels")
end = pd.Timestamp(end_date + timedelta(days=1), tz="Europe/Brussels")

# Country mapping
country_codes = {
    "Portugal": "PT",
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Belgium": "BE",
    "Netherlands": "NL"
}

selected_countries = st.multiselect("🌍 Select countries", list(country_codes.keys()), default=["Portugal", "Spain", "France", "Germany"])

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

if api_key and selected_countries:
    client = EntsoePandasClient(api_key=api_key)

    st.markdown("### 🌻 Select the data you want to load:")
    col1, col2, col3 = st.columns(3)

    # 🔆 Generation
    if col1.button("🔆 Generation"):
        generation_data = [fetch_generation(client, name, country_codes[name]) for name in selected_countries]
        df_gen = pd.concat([df for df in generation_data if not df.empty], ignore_index=True)
        if not df_gen.empty:
            st.subheader("🔆 Generation by source")
            fig = px.area(df_gen, x="Datetime", y="MW", color="Source", facet_col="Country", title="Electricity Generation")
            st.plotly_chart(fig, use_container_width=True)
            csv = df_gen.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Generation CSV", csv, "generation.csv", "text/csv")
        else:
            st.warning("No generation data returned.")

    # 🔋 Load
    if col2.button("🔋 Load"):
        load_data = [fetch_load(client, name, country_codes[name]) for name in selected_countries]
        valid_loads = [df for df in load_data if not df.empty]
        if valid_loads:
            df_load = pd.concat(valid_loads, ignore_index=True)

            # ✅ Correções para colunas
            df_load["MW"] = df_load["MW"].apply(lambda x: float(str(x).strip("[]")))
            df_load["Datetime"] = pd.to_datetime(df_load["Datetime"], utc=True)

            st.subheader("🔋 Load by country")
            fig = px.line(df_load, x="Datetime", y="MW", color="Country", title="Total Load", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            csv = df_load.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Load CSV", csv, "load.csv", "text/csv")
        else:
            st.warning("No load data returned.")

    # 💶 Day-Ahead Price
    if col3.button("💶 Day-Ahead Prices"):
        price_data = [fetch_price(client, name, country_codes[name]) for name in selected_countries]
        valid_prices = [df for df in price_data if not df.empty]
        if valid_prices:
            df_price = pd.concat(valid_prices, ignore_index=True)
            st.subheader("💶 Spot Market Prices by Country")
            fig = px.line(df_price, x=df_price.columns[0], y="Price (€/MWh)", color="Country", title="Day-Ahead Prices", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            csv = df_price.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Price CSV", csv, "prices.csv", "text/csv")
        else:
            st.warning("No price data returned.")
else:
    st.info("Please enter your ENTSO-E token and select at least one country.")
