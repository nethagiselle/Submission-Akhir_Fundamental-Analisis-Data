import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import streamlit as st
from datetime import time
from pathlib import Path
from streamlit_folium import st_folium

sns.set(style="dark")

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']

# ---------------------------------------------------------------------------
def load_data():
    data = pd.read_csv(Path(__file__).parent / "main_data.csv")
    data["datetime"] = pd.to_datetime(data["datetime"], errors="coerce", format="mixed")
    data = data.dropna(subset=["datetime"])
    data["date"] = data["datetime"].dt.date
    data["year"] = data["datetime"].dt.year
    data["month"] = data["datetime"].dt.month
    data["hour"] = data["datetime"].dt.hour
    data["season"] = np.select(
        [data["month"].isin([12, 1, 2]), data["month"].isin([6, 7, 8])],
        ["Musim Dingin", "Musim Panas"], default="Peralihan")
    data["above150"] = data["PM2.5"] > 150
    return data

def create_trend_df(df):
    trend_df = df.resample(rule="D", on="datetime")[["PM2.5", "PM10"]].mean().dropna().reset_index()
    return trend_df

def create_station_df(df):
    station_df = (df.groupby("station")["PM2.5"].mean().reset_index()
                  .rename(columns={"PM2.5": "pm25_avg"})
                  .sort_values(by="pm25_avg", ascending=False))
    return station_df

def create_annual_df(df):
    annual_df = (df.groupby(["station", "year"])["PM2.5"].mean().unstack()
                 .reindex(columns=[2014, 2015, 2016]))
    return annual_df.sort_values(by=2014, ascending=False)

def create_monthly_df(df):
    return df.groupby("month")["above150"].mean().mul(100).reindex(range(1, 13))

def create_hourly_df(df):
    return df.groupby("hour")["above150"].mean().mul(100).reindex(range(24))

def create_wind_rain_df(df):
    sea_df = df[df["season"] != "Peralihan"].copy()
    sea_df["wind_bin"] = pd.cut(sea_df["WSPM"], bins=[-0.01, 1, 2, 3, 4, np.inf],
                                labels=["≤ 1", "1–2", "2–3", "3–4", "> 4"])
    sea_df["rain_status"] = np.where(sea_df["RAIN"] > 0, "Hujan", "Tanpa hujan")
    wind_df = sea_df.groupby(["wind_bin", "season"], observed=True)["PM2.5"].mean().reset_index()
    rain_df = sea_df.groupby(["rain_status", "season"])["PM2.5"].mean().reset_index()
    return sea_df, wind_df, rain_df

all_df = load_data()

# ---------------------------------------------------------------------------
min_date = all_df["date"].min()
max_date = all_df["date"].max()
all_stations = sorted(all_df["station"].unique())

with st.sidebar:
    st.header("Filter Data")

    st.subheader("Date Filter")
    date_range = st.date_input("Date Range", min_value=min_date, max_value=max_date,
                               value=[min_date, max_date])

    st.subheader("Time Filter")
    start_time = st.time_input("Start Time", value=time(0, 0))
    end_time = st.time_input("End Time", value=time(23, 59))

    st.subheader("Station Filter")
    selected_stations = st.multiselect("Select Station(s)", options=all_stations, default=all_stations)

# st.date_input mengembalikan 1 tanggal saja saat pengguna baru memilih tanggal awal
if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Pilih tanggal awal **dan** tanggal akhir pada filter Date Range.")
    st.stop()
start_date, end_date = date_range

if start_time > end_time:
    st.warning("Start Time harus lebih awal dari End Time.")
    st.stop()

main_df = all_df[
    (all_df["date"] >= start_date) & (all_df["date"] <= end_date) &
    (all_df["hour"] >= start_time.hour) & (all_df["hour"] <= end_time.hour) &
    (all_df["station"].isin(selected_stations))
].copy()

if main_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah tanggal, jam, atau stasiun.")
    st.stop()

trend_df = create_trend_df(main_df)
station_df = create_station_df(main_df)
monthly = create_monthly_df(main_df)
hourly = create_hourly_df(main_df)
sea_df, wind_df, rain_df = create_wind_rain_df(main_df)

# ---------------------------------------------------------------------------
st.title("Dashboard Kualitas Udara Beijing :sparkles:")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average PM2.5", f"{main_df['PM2.5'].mean():.1f} µg/m³")
col2.metric("Average PM10", f"{main_df['PM10'].mean():.1f} µg/m³")
col3.metric("Maximum PM2.5", f"{main_df['PM2.5'].max():.0f} µg/m³")
col4.metric("Monitoring Stations", main_df["station"].nunique())

st.subheader("Tren PM2.5 dan PM10 (rata-rata harian)")
fig, ax = plt.subplots(figsize=(16, 6))
ax.plot(trend_df["datetime"], trend_df["PM2.5"], label="PM2.5", linewidth=1.5, color="#90CAF9")
ax.plot(trend_df["datetime"], trend_df["PM10"], label="PM10", linewidth=1.5, color="#FFB74D")
ax.axhline(35, color="#C0392B", ls="--", lw=1)
ax.set_xlabel("Tanggal", fontsize=14)
ax.set_ylabel("Konsentrasi (µg/m³)", fontsize=14)
ax.set_title("Tren PM2.5 dan PM10 dari waktu ke waktu (garis merah = standar tahunan PM2.5: 35)", fontsize=16)
ax.legend(fontsize=12)
ax.grid(alpha=0.3)
st.pyplot(fig)
plt.close(fig)

st.subheader("Rata-Rata PM2.5 per Stasiun")
fig, ax = plt.subplots(figsize=(16, 7))
colors = ["#90CAF9"] + ["#D3D3D3"] * (len(station_df) - 1)
sns.barplot(x="pm25_avg", y="station", hue="station", data=station_df, palette=colors, legend=False, ax=ax)
ax.set_title("Rata-rata PM2.5 per stasiun", fontsize=18)
ax.set_xlabel("Rata-rata PM2.5 (µg/m³)", fontsize=14)
ax.set_ylabel(None)
ax.tick_params(axis="y", labelsize=13)
st.pyplot(fig)
plt.close(fig)

st.header("Pertanyaan Analisis Data")
st.subheader("1. PM2.5 per stasiun, 2014-2016")
annual_df = create_annual_df(all_df[all_df["station"].isin(selected_stations)])
fig, ax = plt.subplots(figsize=(14, 6))
annual_df.plot(kind="bar", ax=ax, color=["#9AA5B1", "#7FA8C9", "#2E6F9E"], width=0.8)
ax.axhline(35, color="#C0392B", ls="--", lw=1)
ax.set_ylabel("Rata-rata PM2.5 (µg/m³)", fontsize=12)
ax.set_xlabel("")
ax.set_title("Rata-rata PM2.5 tahunan per stasiun (garis merah = standar 35)", fontsize=16)
ax.legend(title="Tahun", frameon=False)
plt.xticks(rotation=45, ha="right")
st.pyplot(fig)
plt.close(fig)
st.caption("Grafik ini memakai tahun kalender penuh 2014-2016 dan mengikuti filter stasiun (bukan filter tanggal/jam).")

st.subheader("2. Waktu rawan PM2.5 > 150 µg/m³")
col1, col2 = st.columns(2)
with col1:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(MONTHS, monthly.values, marker="o", linewidth=2, color="#2E6F9E")
    ax.set_title("Per bulan", fontsize=16)
    ax.set_ylabel("% jam PM2.5 > 150")
    ax.set_ylim(0)
    st.pyplot(fig)
    plt.close(fig)
with col2:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(hourly.index, hourly.values, marker="o", linewidth=2, color="#E69F00")
    ax.set_title("Per jam", fontsize=16)
    ax.set_xlabel("Jam")
    ax.set_ylim(0)
    st.pyplot(fig)
    plt.close(fig)

st.subheader("3. Angin dan hujan vs PM2.5 (musim dingin vs musim panas)")
if sea_df.empty:
    st.info("Periode terpilih tidak memuat musim dingin (Des-Feb) atau musim panas (Jun-Agu).")
else:
    hue_order = [s for s in ["Musim Dingin", "Musim Panas"] if s in sea_df["season"].unique()]
    palette = {"Musim Dingin": "#2E6F9E", "Musim Panas": "#E69F00"}
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(16, 5))
    sns.barplot(x="wind_bin", y="PM2.5", hue="season", hue_order=hue_order, data=wind_df, palette=palette, ax=ax[0])
    ax[0].set_title("Kecepatan angin (m/s)", fontsize=15)
    ax[0].set_xlabel(None)
    ax[0].set_ylabel("Rata-rata PM2.5 (µg/m³)")
    ax[0].legend(title=None, frameon=False)
    sns.barplot(x="rain_status", y="PM2.5", hue="season", hue_order=hue_order, data=rain_df, palette=palette, ax=ax[1])
    ax[1].set_title("Hujan", fontsize=15)
    ax[1].set_xlabel(None)
    ax[1].set_ylabel(None)
    ax[1].legend(title=None, frameon=False)
    st.pyplot(fig)
    plt.close(fig)