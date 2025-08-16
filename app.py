#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ==============================================================================
# 1. Imports
# ==============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==============================================================================
# 2. Page Configuration
# ==============================================================================
# Set the page configuration for the Streamlit app
st.set_page_config(
    page_title="COVID-19 Global Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==============================================================================
# 3. Data Loading and Caching
# ==============================================================================
# Use Streamlit's caching to load data only once, improving performance
@st.cache_data
def load_and_clean_data():
    """
    Loads and preprocesses the COVID-19 dataset.
    """
    url = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
    df = pd.read_csv(url)

    # Data cleaning and feature engineering
    df['date'] = pd.to_datetime(df['date'])
    df['people_fully_vaccinated_per_hundred'] = df['people_fully_vaccinated_per_hundred'].fillna(0)
    df['new_deaths_smoothed_per_million'] = (df.groupby('location')['new_deaths']
                                              .transform(lambda x: x.rolling(7).mean()) / df['population']) * 1_000_000
    
    # Filter out non-country aggregate data
    non_countries = ['World', 'High income', 'Upper middle income', 'Lower middle income', 'Low income', 'European Union', 'Asia', 'Africa', 'North America', 'South America', 'Oceania']
    df = df[~df['location'].isin(non_countries)]
    
    return df

# Load the data using the function
df_covid = load_and_clean_data()


# ==============================================================================
# 4. App Title and Introduction
# ==============================================================================
st.title("🌍 COVID-19 Interactive Global Dashboard")
st.markdown("This dashboard provides an interactive way to explore the COVID-19 pandemic data. Use the sidebar to filter data.")


# ==============================================================================
# 5. Sidebar Controls
# ==============================================================================
st.sidebar.header("Dashboard Controls")

# Multiselect for countries for the time-series chart
default_countries = ['United States', 'India', 'Brazil', 'United Kingdom', 'Germany']
selected_countries = st.sidebar.multiselect(
    'Select Countries for Time-Series Plot',
    options=sorted(df_covid['location'].unique()),
    default=default_countries
)

# Date slider for the geospatial map
min_date = df_covid['date'].min().date()
max_date = df_covid['date'].max().date()

selected_date = st.sidebar.slider(
    "Select Date for World Map",
    min_value=min_date,
    max_value=max_date,
    value=datetime(2022, 7, 1).date(), # Default date
    format="YYYY-MM-DD"
)


# ==============================================================================
# 6. Main Dashboard Content
# ==============================================================================
# --- Key Performance Indicators (KPIs) ---
st.header("Global Overview")
latest_data = df_covid[df_covid['date'] == df_covid['date'].max()]
global_cases = latest_data['total_cases'].sum()
global_deaths = latest_data['total_deaths'].sum()

col1, col2 = st.columns(2)
col1.metric("Total Confirmed Cases (Worldwide)", f"{int(global_cases):,}")
col2.metric("Total Deaths (Worldwide)", f"{int(global_deaths):,}")
st.markdown("---") # Visual separator

# --- Time-Series Plot ---
st.header("📈 Time-Series Analysis of Daily Deaths")
if selected_countries:
    df_plot = df_covid[df_covid['location'].isin(selected_countries)]
    fig_line = px.line(
        df_plot,
        x='date',
        y='new_deaths_smoothed_per_million',
        color='location',
        title='7-Day Average of Daily Deaths per Million People',
        labels={'new_deaths_smoothed_per_million': 'Daily Deaths per Million (Smoothed)', 'date': 'Date'}
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("Please select at least one country from the sidebar to display the time-series plot.")

# --- Geospatial Map ---
st.header("🗺️ Geospatial Map of Vaccination Rates")
map_data = df_covid[df_covid['date'] == pd.to_datetime(selected_date)]

fig_map = px.choropleth(
    map_data,
    locations="iso_code",
    color="people_fully_vaccinated_per_hundred",
    hover_name="location",
    color_continuous_scale=px.colors.sequential.Plasma,
    title=f"Percentage of Population Fully Vaccinated as of {selected_date}",
    range_color=(0, 100) # Keep color scale consistent
)
st.plotly_chart(fig_map, use_container_width=True)

