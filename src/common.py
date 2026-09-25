import sqlite3
from pathlib import Path

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "sales_and_returns.db"
SCRIPTS = ROOT / "scripts"


@st.cache_data
def _run(sql: str, db_mtime: float, params: tuple) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=dict(params))


def query(script: str, **params) -> pd.DataFrame:
    return _run((SCRIPTS / script).read_text(), DB_PATH.stat().st_mtime, tuple(sorted(params.items())))


def bar_chart(df: pd.DataFrame, category: str, value: str, horizontal: bool, select: str | None = None,
              selected: str | None = None):
    if select:
        df = df.assign(Selected=True if selected is None else df[category] == selected)
    tooltip = [category, alt.Tooltip(value, format=",")]
    if horizontal:
        enc = {"y": alt.Y(category, sort="-x", title=None), "x": alt.X(value, title=None)}
    else:
        enc = {"x": alt.X(category, title=None), "y": alt.Y(value, title=None)}
    chart = alt.Chart(df).mark_bar(cursor="pointer" if select else "default").encode(tooltip=tooltip, **enc)
    if select:
        pick = alt.selection_point(name="pick", fields=[category], on="click", clear="click[!event.item]")
        params = [pick]
        if select == "drill":
            params.append(alt.selection_point(name="drill", fields=[category], on="dblclick", clear=False))
        chart = chart.add_params(*params).encode(opacity=alt.condition(alt.datum.Selected, alt.value(1), alt.value(0.55)))
    return chart.properties(height=350)


def store_line_chart(df: pd.DataFrame, amount_label: str, top_n: int = 4, selectable: bool = False,
                     selected_month: str | None = None):
    top = df.groupby("Store")["Amount"].sum().nlargest(top_n).index.tolist()
    df = df[df["Store"].isin(top)].assign(
        MonthName=lambda d: pd.to_datetime(d["Month"] + "-01").dt.strftime("%b"),
        Selected=lambda d: True if selected_month is None else d["Month"] == selected_month)
    order = df.sort_values("Month")["MonthName"].unique().tolist()
    base = alt.Chart(df).encode(
        x=alt.X("MonthName:O", sort=order, title="Date", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Amount:Q", title=amount_label, axis=alt.Axis(format="~s")),
        color=alt.Color("Store:N", sort=top, title="Store", scale=alt.Scale(range=["#F2B632", "#E8862A", "#D9522B", "#C2306B"])),
        tooltip=["Store", "MonthName", alt.Tooltip("Amount", format=",")],
    )
    lines = base.mark_line(interpolate="monotone", strokeWidth=3)
    points = base.mark_point(filled=True, size=70, cursor="pointer" if selectable else "default")
    if selectable:
        pick = alt.selection_point(name="pick", fields=["Month"], on="click", clear="click[!event.item]")
        points = points.add_params(pick).encode(opacity=alt.condition(alt.datum.Selected, alt.value(1), alt.value(0.35)))
    labels = base.mark_text(dy=-10, fontSize=11).encode(text=alt.Text("Amount:Q", format=".2~s"))
    return (lines + points + labels).properties(height=380, title=f"{amount_label} by Date and Store (top {top_n} stores)")


def store_map(df: pd.DataFrame, amount_label: str, color=(0, 120, 212, 160), height: int = 350, key: str | None = None):
    df = df.dropna(subset=["Latitude", "Longitude"]).assign(
        Radius=lambda d: 400 + 1600 * d["Amount"] / d["Amount"].max(),
        AmountText=lambda d: d["Amount"].map("${:,.0f}".format),
    )
    layer = pdk.Layer(
        "ScatterplotLayer", df, id="stores", get_position=["Longitude", "Latitude"], get_radius="Radius",
        get_fill_color=list(color), get_line_color=[255, 255, 255], line_width_min_pixels=1,
        stroked=True, pickable=True,
    )
    view = pdk.ViewState(latitude=df["Latitude"].mean(), longitude=df["Longitude"].mean(), zoom=9.5)
    tooltip = {"html": f"<b>{{Store}}</b> ({{Type}})<br/>{amount_label}: {{AmountText}}"}
    deck = pdk.Deck(layers=[layer], initial_view_state=view, tooltip=tooltip, map_style="light")
    if key is None:
        return st.pydeck_chart(deck, height=height)
    return st.pydeck_chart(deck, height=height, on_select="rerun", selection_mode="single-object", key=key)
