import streamlit as st
import requests
from skyfield.api import load, EarthSatellite
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Streamlit configuration
st.set_page_config(layout="wide")
st.title("🌍 Live Satellite Tracker")
st.markdown("Track the ISS, NOAA 15, TIANMU-1 14, METEOR-M 2 4")

# Customizable location input
col1, col2 = st.columns(2)
with col1:
    my_lat = st.number_input("Your Latitude", value=16.8409)
with col2:
    my_lon = st.number_input("Your Longitude", value=96.1735)

# --- Fetch TLE Data Functions ---
@st.cache_data(ttl=3600)
def get_tle_iss():
    url = "https://celestrak.org/NORAD/elements/stations.txt"
    lines = requests.get(url).text.strip().split("\n")
    for i in range(0, len(lines), 3):
        if "ISS (ZARYA)" in lines[i]:
            return lines[i], lines[i+1], lines[i+2]
    raise ValueError("ISS not found")

@st.cache_data(ttl=3600)
def get_tle_noaa():
    url = "https://celestrak.org/NORAD/elements/weather.txt"
    lines = requests.get(url).text.strip().split("\n")
    for i in range(0, len(lines), 3):
        if "NOAA 15" in lines[i]:
            return lines[i], lines[i+1], lines[i+2]
    raise ValueError("NOAA 15 not found")

@st.cache_data(ttl=3600)
def get_tle_tianmu():
    url = "https://celestrak.org/NORAD/elements/weather.txt"
    lines = requests.get(url).text.strip().split("\n")
    for i in range(0, len(lines), 3):
        if "TIANMU-1 14" in lines[i]:
            return lines[i], lines[i+1], lines[i+2]
    raise ValueError("TIANMU-1 14 not found")

@st.cache_data(ttl=3600)
def get_tle_meteor():
    url = "https://celestrak.org/NORAD/elements/weather.txt"
    lines = requests.get(url).text.strip().split("\n")
    for i in range(0, len(lines), 3):
        if "METEOR-M 2 4" in lines[i] or "METEOR-M2 4" in lines[i]:
            return lines[i], lines[i+1], lines[i+2]
    raise ValueError("METEOR-M2 4 not found")

# --- Satellite data ---
def get_satellite_data(satellite, ts):
    time_now = ts.now()
    geocentric = satellite.at(time_now)
    subpoint = geocentric.subpoint()
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees
    alt = subpoint.elevation.km
    velocity = geocentric.velocity.km_per_s
    speed = np.linalg.norm(velocity)

    times = ts.utc(time_now.utc_datetime().year,
                   time_now.utc_datetime().month,
                   time_now.utc_datetime().day,
                   np.linspace(0, 24, 100))
    positions = [satellite.at(t).subpoint() for t in times]
    lats = [pos.latitude.degrees for pos in positions]
    lons = [pos.longitude.degrees for pos in positions]

    return lat, lon, alt, speed, lats, lons

# --- Main ---
def main():
    ts = load.timescale()

    # Load all satellites
    name_iss, tle1_iss, tle2_iss = get_tle_iss()
    name_noaa, tle1_noaa, tle2_noaa = get_tle_noaa()
    name_tianmu, tle1_tianmu, tle2_tianmu = get_tle_tianmu()
    name_meteor, tle1_meteor, tle2_meteor = get_tle_meteor()

    sat_iss = EarthSatellite(tle1_iss, tle2_iss, name_iss, ts)
    sat_noaa = EarthSatellite(tle1_noaa, tle2_noaa, name_noaa, ts)
    sat_tianmu = EarthSatellite(tle1_tianmu, tle2_tianmu, name_tianmu, ts)
    sat_meteor = EarthSatellite(tle1_meteor, tle2_meteor, name_meteor, ts)

    satellites = [
        {"sat": sat_iss, "color": "yellow"},
        {"sat": sat_noaa, "color": "red"},
        {"sat": sat_tianmu, "color": "magenta"},
        {"sat": sat_meteor, "color": "lime"}
    ]

    fig, ax = plt.subplots(figsize=(12, 6))
    m = Basemap(projection='cyl', resolution='c')
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary(fill_color='midnightblue')
    m.fillcontinents(color='forestgreen', lake_color='darkgreen')
    m.drawparallels(np.arange(-90., 91., 30.))
    m.drawmeridians(np.arange(-180., 181., 60.))

    # Plot your location
    x_my, y_my = m(my_lon, my_lat)
    ax.scatter(x_my, y_my, color='white', marker='^', s=100, label="Your Location")

    # Plot satellites
    for item in satellites:
        sat = item["sat"]
        color = item["color"]
        lat, lon, alt, speed, path_lats, path_lons = get_satellite_data(sat, ts)
        x, y = m(lon, lat)
        ax.scatter(x, y, color=color, s=100, label=sat.name)
        path_x, path_y = m(path_lons, path_lats)
        ax.plot(path_x, path_y, linestyle='--', color=color)

        # Display data below the plot
        st.markdown(f"**{sat.name}** — Lat: `{lat:.2f}°`, Lon: `{lon:.2f}°`, Alt: `{alt:.1f} km`, Speed: `{speed:.2f} km/s`")

    ax.legend(loc='lower left', fontsize=9)
    st.pyplot(fig)

# Reload Button (Streamlit-style)
if st.button("🔁 Reload Satellite Data"):
    st.rerun()

# Run app
main()
