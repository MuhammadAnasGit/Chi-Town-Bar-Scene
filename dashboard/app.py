import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Chi-Town Bar Scene", page_icon="🍺", layout="wide")
from pathlib import Path
CLOUD_FILE = "data/silver/bars.parquet"
DATA = CLOUD_FILE if Path(CLOUD_FILE).exists() else "C:/barscene-data/silver/bars.parquet"

@st.cache_data
def load():
    df = duckdb.sql(f"SELECT * FROM '{DATA}'").df()
    df["first_licensed"] = pd.to_datetime(df["first_licensed"])
    return df

bars = load()

st.title("🍺 Chi-Town Bar Scene")
st.caption("Every licensed bar and alcohol-serving restaurant in Chicago · Source: City of Chicago business licenses")

# --- Filters (left sidebar) ---
types = st.sidebar.multiselect("Venue type", sorted(bars.venue_type.unique()), default=["Bar / Tavern"])
areas = st.sidebar.multiselect("Neighborhood", sorted(bars.community_area.dropna().unique()))
late_only = st.sidebar.checkbox("Open late only")

view = bars[bars.venue_type.isin(types)]
if areas:
    view = view[view.community_area.isin(areas)]
if late_only:
    view = view[view.open_late]
open_now = view[view.is_open]

# --- Headline numbers ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Open now", f"{len(open_now):,}")
c2.metric("Open late", f"{int(open_now.open_late.sum()):,}")
c3.metric("Closed over the years", f"{int((~view.is_open).sum()):,}")
c4.metric("Neighborhoods", open_now.community_area.nunique())

# --- Map ---
st.subheader("🗺️ Where they are")
st.map(open_now.dropna(subset=["lat", "lng"]), latitude="lat", longitude="lng", size=25)

# --- Charts ---
left, right = st.columns(2)
with left:
    st.subheader("🏆 Top neighborhoods")
    top = open_now.groupby("community_area").size().sort_values(ascending=False).head(15)
    st.bar_chart(top, horizontal=True)
with right:
    st.subheader("📈 New places per year")
    yearly = view.first_licensed.dt.year.value_counts().sort_index()
    st.line_chart(yearly[yearly.index >= 2003])

# --- Searchable list ---
st.subheader("📋 All open places")
st.dataframe(
    open_now[["bar_name", "address", "community_area", "venue_type", "open_late", "first_licensed"]]
    .sort_values("bar_name"),
    hide_index=True, use_container_width=True,
)