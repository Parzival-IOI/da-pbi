import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from common import query, store_map

ORANGE = "#FFA800"
GREY = "#C8C8C8"
FORECAST_WEEKS = 4


def _what_if(df: pd.DataFrame, target: float, rate: float) -> pd.DataFrame:
    keep = min(1.0, target / rate) if rate > 0 else 1.0
    return df.assign(extra=df["returned"] * (1 - keep), wif=lambda d: d["sold"] + d["returned"] * (1 - keep))


def _forecast_chart(daily: pd.DataFrame, uplift: float):
    actual = daily.assign(Series="Net Sales")[["date", "sold", "Series"]].rename(columns={"sold": "value"})
    recent = daily["sold"].tail(8)
    last_date, last_val = daily["date"].iloc[-1], daily["sold"].iloc[-1]
    steps = np.arange(0, FORECAST_WEEKS + 1)
    fc = pd.DataFrame({
        "date": last_date + pd.to_timedelta(steps * 7, unit="D"),
        "value": np.where(steps == 0, last_val, recent.mean() * uplift),
        "Series": "Forecast",
    })
    spread = 1.5 * recent.std(ddof=0) * uplift * (1 + 0.15 * steps)
    band = fc.assign(lo=(fc["value"] - spread).clip(lower=0), hi=fc["value"] + spread)

    color = alt.Color("Series:N", title=None, legend=alt.Legend(orient="top"),
                      scale=alt.Scale(domain=["Net Sales", "Forecast"], range=[ORANGE, "#222222"]))
    x = alt.X("date:T", title="Date", axis=alt.Axis(format="%b"))
    y = alt.Y("value:Q", title=None, axis=alt.Axis(format="~s"))
    tip = [alt.Tooltip("date:T", format="%b %d, %Y"), "Series", alt.Tooltip("value:Q", format=",.0f")]
    lines = alt.Chart(pd.concat([actual, fc])).mark_line(strokeWidth=2.5).encode(x=x, y=y, color=color, tooltip=tip)
    area = alt.Chart(band).mark_area(opacity=0.25, color="#888888").encode(x="date:T", y="lo:Q", y2="hi:Q")
    rule = alt.Chart(pd.DataFrame({"date": [last_date]})).mark_rule(color="#888888").encode(x="date:T")
    return (area + lines + rule).properties(height=330)


def _extra_profit_chart(daily: pd.DataFrame):
    long = daily.rename(columns={"sold": "Net Sales", "extra": "Extra Profit"}).melt(
        id_vars="date", value_vars=["Net Sales", "Extra Profit"], var_name="Series", value_name="value")
    return alt.Chart(long).mark_bar(size=9).encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b")),
        y=alt.Y("value:Q", title=None, axis=alt.Axis(format="~s")),
        color=alt.Color("Series:N", title=None, sort=["Net Sales", "Extra Profit"], legend=alt.Legend(orient="top"),
                        scale=alt.Scale(domain=["Net Sales", "Extra Profit"], range=[GREY, ORANGE])),
        order=alt.Order("Series:N", sort="descending"),
        tooltip=[alt.Tooltip("date:T", format="%b %d, %Y"), "Series", alt.Tooltip("value:Q", format=",.0f")],
    ).properties(height=330, title="Net Sales and Extra Profit by Date")


def render(dim: str, item: str):
    info = query("return_rate/item_info.sql", dim=dim, item=item)
    if info.empty:
        st.warning(f"No {dim.lower()} named '{item}' was found.")
        return
    stores = query("return_rate/by_store.sql", dim=dim, item=item)
    daily = query("return_rate/by_date.sql", dim=dim, item=item)
    daily = daily.assign(date=pd.to_datetime(daily["sale_date"]))

    sold, returned = stores["sold"].sum(), stores["returned"].sum()
    rate = returned / (sold + returned) if sold + returned else 0.0

    st.markdown("<style>[data-testid='stMetricValue']{font-size:1.7rem}</style>", unsafe_allow_html=True)
    left, mid, right = st.columns([1, 1.3, 1.4])

    with mid:
        st.markdown("**What If...**")
        target_pct = st.slider("We decrease our % return rate to", 0, 60, 3, format="%d%%")
    target = target_pct / 100
    stores = _what_if(stores, target, rate)
    daily = _what_if(daily, target, rate)
    extra, wif = stores["extra"].sum(), stores["wif"].sum()

    with left, st.container(border=True):
        st.subheader(item)
        if dim == "Product":
            st.caption(info["Category"].iloc[0])
            i1, i2 = st.columns(2)
            i1.image(info["icon_image"].iloc[0], width="stretch")
            i2.image(info["board_image"].iloc[0], width="stretch")
        else:
            st.caption(f"{len(info)} products")
            st.image(info["category_image"].iloc[0], width="stretch")
        st.metric("Return Rate", f"{rate:.1%}")
        weekly = daily.assign(rate=lambda d: d["returned"] / (d["sold"] + d["returned"]))
        st.altair_chart(
            alt.Chart(weekly).mark_bar(color=ORANGE, size=8).encode(
                x=alt.X("date:T", title=None, axis=alt.Axis(format="%b %Y", tickCount=5)),
                y=alt.Y("rate:Q", title=None, axis=alt.Axis(format="%")),
                tooltip=[alt.Tooltip("date:T", format="%b %d, %Y"), alt.Tooltip("rate:Q", title="Return rate", format=".1%")],
            ).properties(height=160),
            width="stretch")

    with mid, st.container(border=True):
        st.subheader('Net Sales vs "What If" Analysis')
        view = st.segmented_control("Store view", ["Visual", "Map"], default="Visual",
                                    key="rr_store_view", label_visibility="collapsed") or "Visual"
        if view == "Visual":
            table = stores[["Store", "sold", "wif", "extra"]].rename(
                columns={"sold": "Net Sales", "wif": "WIF Forecast", "extra": "WIF Profit"})
            table.loc[len(table)] = ["Total", sold, wif, extra]
            st.dataframe(table, hide_index=True, width="stretch", height=420,
                         column_config={c: st.column_config.NumberColumn(format="dollar")
                                        for c in ["Net Sales", "WIF Forecast", "WIF Profit"]})
        else:
            store_map(stores.assign(Amount=stores["wif"]), "WIF Forecast", color=(255, 214, 0, 190), height=420)

    with right:
        k1, k2 = st.columns(2)
        k1.metric("Extra Profit", f"${extra:,.0f}", border=True)
        k2.metric("Net Sales (Forecast)", f"${wif:,.0f}", border=True)
        with st.container(border=True):
            st.subheader('"What If" Analysis Forecast')
            rview = st.segmented_control("Forecast view", ["Forecast", "Extra Profit"], default="Forecast",
                                         key="rr_forecast_view", label_visibility="collapsed") or "Forecast"
            if rview == "Forecast":
                uplift = wif / sold if sold else 1.0
                st.altair_chart(_forecast_chart(daily, uplift), width="stretch")
            else:
                st.altair_chart(_extra_profit_chart(daily), width="stretch")
