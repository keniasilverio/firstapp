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
import matplotlib.pyplot as plt


st.set_page_config(layout="wide")
st.title("🌻 Helianthus – ENTSO-E + Solar Insights")

# Sidebar menu
sections = ["📊 Dashboard", "🔆 Generation", "🔋 Load", "💶 Day-Ahead Prices", "ℹ️ EEG Info", "🌞 PVGIS Monthly", "☀️ PVGIS Overview", "🔐 Project Management"]
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
        - ℹ️ EEG (FIT) incentives for rooftop solar  
        - ☀️ PVGIS Overview
        - 🌞 PVGIS Monthly
        - 🔐 Project Management
       

        > Created by **Kenia Silverio**  
        👉 [LinkedIn](https://www.linkedin.com/in/kenia-silverio/)
        '''
    )

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
    
elif selected_section == "🌞 PVGIS Monthly":
    st.subheader("☀️ Monthly Solar Irradiation – Germany")

    city_coords = {
        "Berlin": (52.52, 13.405),
        "Hamburg": (53.5511, 9.9937),
        "Munich": (48.1351, 11.582),
        "Frankfurt": (50.1109, 8.6821),
        "Cologne": (50.9375, 6.9603)
    }
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    selected_city = st.selectbox("📍 Select a German city", list(city_coords.keys()))
    lat, lon = city_coords[selected_city]

    def get_monthly_irradiation(lat, lon):
        url = (
            f"https://re.jrc.ec.europa.eu/api/v5_2/PVcalc?"
            f"lat={lat}&lon={lon}&peakpower=1&loss=14&angle=35&aspect=0"
            f"&mountingplace=building&pvtechchoice=crystSi&radiation_db=PVGIS-SARAH2"
            f"&optimalangles=0&usehorizon=1&monthdata=1&outputformat=json"
        )
        r = requests.get(url)
        data = r.json()
        monthly_data = data["outputs"]["monthly"]["fixed"]
        irradiation = [month["H(i)_m"] for month in monthly_data]
        return irradiation

    irradiation = get_monthly_irradiation(lat, lon)

    df_irr = pd.DataFrame({
        "Month": months,
        "Irradiation (kWh/m²)": irradiation
    })

    col1, col2 = st.columns([2, 1])
    with col1:
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(df_irr["Month"], df_irr["Irradiation (kWh/m²)"], color="gold")
        ax.set_title(f"☀️ Monthly Solar Irradiation – {selected_city}")
        ax.set_ylabel("kWh/m²")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.5)
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 2, f"{height:.0f}", ha='center')
        st.pyplot(fig)

    with col2:
        st.markdown(f"### 📋 Irradiation Table – {selected_city}")
        st.dataframe(df_irr.style.format({"Irradiation (kWh/m²)": "{:.1f}"}), use_container_width=True)

elif selected_section == "☀️ PVGIS Overview":
    import streamlit.components.v1 as components

    st.subheader("☀️ Solar Irradiation Overview – Germany")

    # Dados simulados
    data = {
        "City": ["Berlin", "Hamburg", "Munich", "Frankfurt", "Cologne"],
        "Irradiation (kWh/m²)": [118.4, 109.6, 126.7, 122.1, 115.9]
    }
    df = pd.DataFrame(data)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🗺️ Map of Monthly Solar Irradiation")
        components.html("pvgis_overview_map.html", height=600)

    with col2:
        st.markdown("### 📋 Comparison Table")
        st.dataframe(df.sort_values("Irradiation (kWh/m²)", ascending=False), use_container_width=True)

elif selected_section == "🔐 Project Management":
    import streamlit as st
    import pandas as pd

    st.subheader("🔐 Restricted Project Management Area")

    password = st.text_input("Enter access password", type="password")
    if password == "VODASUN":
        st.success("Access granted. Welcome to the Project Management Area.")

        st.markdown("### 📂 Upload your Excel project file")
        uploaded_file = st.file_uploader("Upload file", type=["xlsx"])

        if uploaded_file:
            df = pd.read_excel(uploaded_file)

            # Tarifas FIT
            tarifas_ate_400 = [
                {'faixa_kWp': 10, 'fit_tarifa': 12.99},
                {'faixa_kWp': 30, 'fit_tarifa': 10.96},
                {'faixa_kWp': 60, 'fit_tarifa': 12.47},
                {'faixa_kWp': float('inf'), 'fit_tarifa': 10.63}
            ]

            tarifas_acima_400 = [
                {'faixa_kWp': 10, 'fit_tarifa': 12.99},
                {'faixa_kWp': 30, 'fit_tarifa': 10.96},
                {'faixa_kWp': 60, 'fit_tarifa': 12.47},
                {'faixa_kWp': 300, 'fit_tarifa': 10.63},
                {'faixa_kWp': float('inf'), 'fit_tarifa': 9.36}
            ]

            def calcular_fit_tarifa(tamanho):
                total_tarifa = 0
                restante = tamanho
                faixas = tarifas_ate_400 if tamanho <= 400 else tarifas_acima_400

                for faixa in faixas:
                    if restante > 0:
                        kWp_faixa = min(faixa['faixa_kWp'], restante)
                        total_tarifa += kWp_faixa * faixa['fit_tarifa']
                        restante -= kWp_faixa

                tarifa_media = total_tarifa / tamanho
                return round(tarifa_media, 2)

            if "Tamanho_kWp" in df.columns:
                df["FIT_Tarifa_2025 (ct/kWh)"] = df["Tamanho_kWp"].apply(calcular_fit_tarifa)
                st.success("✅ FIT tariff successfully calculated for all projects.")
                st.dataframe(df)

                # Download
                st.download_button(
                    label="📥 Download FIT tariff results",
                    data=df.to_excel(index=False, engine='openpyxl'),
                    file_name="projetos_fit_2025_calculado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Column 'Tamanho_kWp' not found in uploaded file.")
    else:
        st.warning("This section is protected. Please enter the correct password.")


