import streamlit as st
import pandas as pd
import plotly.express as px
from entsoe import EntsoePandasClient
from datetime import datetime, timedelta
import pytz
import time

st.set_page_config(layout="wide")
st.title("🌻 Helianthus – ENTSO-E Energy Dashboard")

st.markdown(
    '''
    Welcome to the **Helianthus** energy dashboard.  
    Explore public data from ENTSO-E for Portugal, Spain, France, and Germany:

    - 🔆 Generation by energy source  
    - 🔋 Total electricity load  
    - 💶 Day-ahead spot prices  

    > Created by **Kenia Silverio**  
    👉 [LinkedIn](https://www.linkedin.com/in/kenia-silverio/)
    '''
)

api_key = st.text_input("🔐 Paste your ENTSO-E API token here:", type="password")

# 📅 Date range selector (default: last 7 days)
today = datetime.now()
default_start = today - timedelta(days=7)
start_date, end_date = st.date_input(
    "📅 Select the date range", 
    value=(default_start, today), 
    max_value=today
)

# Timezone conversion
start = pd.Timestamp(start_date, tz="Europe/Brussels")
end = pd.Timestamp(end_date + timedelta(days=1), tz="Europe/Brussels")

countries = {
    "Portugal": "PT",
    "Spain": "ES",
    "France": "FR",
    "Germany": "DE"
}

def retry_function(func, retries=2, delay=2):
    for i in range(retries):
        try:
            return func()
        except Exception as e:
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise e

def fetch_generation(client, country_name, code):
    try:
        with st.spinner(f"⚡ Loading generation data for {country_name}..."):
            def call():
                gen = client.query_generation(code, start=start, end=end, psr_type=None)
                if isinstance(gen.columns, pd.MultiIndex):
                    gen.columns = gen.columns.get_level_values(0)
                df = gen.reset_index()
                df = df.melt(id_vars=df.columns[0], var_name="Source", value_name="MW")
                df.columns = ["Datetime", "Source", "MW"]
                df["Country"] = country_name
                return df
            return retry_function(call)
    except Exception as e:
        st.warning(f"⚠️ Generation - {country_name}: {e}")
        return pd.DataFrame()

def fetch_load(client, country_name, code):
    try:
        with st.spinner(f"🔋 Loading load data for {country_name}..."):
            def call():
                load = client.query_load(code, start=start, end=end)
                df = pd.DataFrame()
                df["Datetime"] = load.index
                df["MW"] = list(load.values)
                df["Country"] = country_name
                return df
            return retry_function(call)
    except Exception as e:
        st.warning(f"⚠️ Load - {country_name}: {e}")
        return pd.DataFrame()

def fetch_price(client, country_name, code):
    try:
        with st.spinner(f"💶 Loading price data for {country_name}..."):
            return retry_function(lambda: (
                client.query_day_ahead_prices(code, start=start, end=end)
                .reset_index()
                .rename(columns={0: "Price (€/MWh)"})
                .assign(Country=country_name)
            ))
    except Exception as e:
        st.warning(f"⚠️ Price - {country_name}: {e}")
        return pd.DataFrame()

if api_key:
    client = EntsoePandasClient(api_key=api_key)

    st.markdown("### 🌻 Choose what data you want to load:")

    col1, col2, col3 = st.columns(3)

    if col1.button("🔆 Load Generation"):
        all_gen = [fetch_generation(client, name, code) for name, code in countries.items()]
        gen_df = pd.concat([df for df in all_gen if not df.empty], ignore_index=True)
        if not gen_df.empty:
            st.subheader("🔆 Generation by Energy Source")
            selected_country = st.selectbox("Select a country", gen_df["Country"].unique(), key="gen")
            chart_df = gen_df[gen_df["Country"] == selected_country]
            fig = px.area(chart_df, x="Datetime", y="MW", color="Source", title=f"Generation - {selected_country}")
            st.plotly_chart(fig, use_container_width=True)
            csv = gen_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV – Generation", csv, "generation.csv", "text/csv")
        else:
            st.warning("No generation data available.")

    if col2.button("🔋 Load Total Load"):
        all_load = [fetch_load(client, name, code) for name, code in countries.items()]
        valid_load = [df for df in all_load if not df.empty]
        if valid_load:
            load_df = pd.concat(valid_load, ignore_index=True)
            st.subheader("🔋 Electricity Load by Country")
            fig2 = px.line(load_df, x="Datetime", y="MW", color="Country", title="Total Load", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
            csv = load_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV – Load", csv, "load.csv", "text/csv")
        else:
            st.warning("No load data available.")

    if col3.button("💶 Load Day-Ahead Prices"):
        all_prices = [fetch_price(client, name, code) for name, code in countries.items()]
        valid_prices = [df for df in all_prices if not df.empty]
        if valid_prices:
            price_df = pd.concat(valid_prices, ignore_index=True)
            st.subheader("💶 Day-Ahead Prices by Country")
            fig3 = px.line(price_df, x=price_df.columns[0], y="Price (€/MWh)", color="Country", title="Spot Prices", markers=True)
            st.plotly_chart(fig3, use_container_width=True)
            csv = price_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV – Prices", csv, "prices.csv", "text/csv")
        else:
            st.warning("No price data available.")
else:
    st.info("Please enter your ENTSO-E token to activate the dashboard.")
