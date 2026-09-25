import streamlit as st

import return_rate
from common import bar_chart, query, store_line_chart, store_map

st.set_page_config(page_title="Sales Report", layout="wide")


NO_FILTER = {"dim": "", "item": "", "store_id": 0, "month": ""}


def _toggle(label: str, options: list[str], key: str) -> str:
    return st.segmented_control(label, options, default=options[0], key=key,
                                label_visibility="collapsed", persist_state="session") or options[0]


def _open_return_rate(folder: str, dim: str, item: str):
    st.session_state["rr_origin"] = folder
    st.switch_page(RETURN_RATE_PAGE, query_params={"dim": dim, "item": item})


def _bump(folder: str, groups: tuple[str, ...]):
    for g in groups:
        st.session_state[f"{folder}_fv"][g] += 1


def _selection(key: str) -> dict:
    state = st.session_state.get(key)
    return (state.get("selection") if state else None) or {}


def _picked(key: str, field: str):
    rows = _selection(key).get("pick") or []
    return rows[0][field] if rows else None


def render(title: str, folder: str, amount_label: str, amount_script: str, units_script: str,
           sales_col: str, units_col: str):
    st.title(title)
    vers = st.session_state.setdefault(f"{folder}_fv", {"cat": 0, "store": 0, "month": 0})

    def k(name: str, group: str) -> str:
        return f"{folder}_{name}_{vers[group]}"

    c1, c2 = st.columns(2)
    banner = st.container()
    left, right = st.columns(2)
    cat_card = left.container(border=True)
    store_card = right.container(border=True)
    month_card = st.container(border=True)

    with cat_card:
        st.subheader("Category breakdown")
        b1, b2 = st.columns(2)
        with b1:
            dim = _toggle("Group by", ["Category", "Product"], f"{folder}_cat_dim")
        with b2:
            view = _toggle("View", ["Visual", "Tabular"], f"{folder}_cat_view")
    with store_card:
        st.subheader("Store breakdown")
        store_view = _toggle("Store view", ["Visual", "Map"], f"{folder}_store_view")
    with month_card:
        st.subheader(f"{amount_label} per month")
        month_view = _toggle("Month view", ["Month", "Month & Store"], f"{folder}_month_view")

    # Selections made in the previous run drive this run's filters.
    all_stores = query(f"{folder}/store_breakdown.sql", **NO_FILTER)
    store_ids = dict(zip(all_stores.iloc[:, 1], all_stores.iloc[:, 0]))
    cat_names = set(query(f"{folder}/{dim.lower()}_breakdown.sql", **NO_FILTER).iloc[:, 0])
    months = set(query(f"{folder}/net_sales_per_month.sql", **NO_FILTER).iloc[:, 0])

    if view == "Visual":
        cat_item = _picked(k("cat_chart", "cat"), "Category")
    else:
        rows = _selection(k("cat_table", "cat")).get("rows") or []
        names = st.session_state.get(k("cat_names", "cat"), [])
        cat_item = names[rows[0]] if rows and rows[0] < len(names) else None
    if store_view == "Visual":
        store_name = _picked(k("store_chart", "store"), "Store")
    else:
        objs = (_selection(k("store_map", "store")).get("objects") or {}).get("stores") or []
        store_name = objs[0]["Store"] if objs else None
    month = _picked(k("month_chart", "month") if month_view == "Month" else k("month_line", "month"), "Month")

    cat_item = cat_item if cat_item in cat_names else None
    store_name = store_name if store_name in store_ids else None
    month = month if month in months else None
    F = {"dim": dim if cat_item else "", "item": cat_item or "",
         "store_id": int(store_ids[store_name]) if store_name else 0, "month": month or ""}

    active = [(g, f"{label} {value}") for g, label, value in
              [("cat", dim.lower(), cat_item), ("store", "store", store_name), ("month", "month", month)] if value]
    if active:
        with banner:
            cols = st.columns([1] + [2.4] * len(active) + [1.5, 0.1 + 1.5 * (3 - len(active))])
            cols[0].markdown("**Filters:**")
            for col, (g, text) in zip(cols[1:], active):
                col.button(f"\u2715 {text}", key=f"{folder}_clear_{g}", on_click=_bump, args=(folder, (g,)))
            cols[len(active) + 1].button("Clear all", key=f"{folder}_clear_all", on_click=_bump,
                                         args=(folder, tuple(vers)))

    amount = query(f"{folder}/{amount_script}", **F).iloc[0, 0]
    units = query(f"{folder}/{units_script}", **F).iloc[0, 0]
    c1.metric(amount_label, f"${amount or 0:,.0f}", border=True)
    c2.metric("Units", f"{units or 0:,.0f}", border=True)

    with cat_card:
        cat_full = query(f"{folder}/{dim.lower()}_breakdown.sql", **{**F, "dim": "", "item": ""}).iloc[:, [0, 2, 3]]
        cat_full.columns = [dim, sales_col, units_col]
        drill = None
        if view == "Visual":
            cat = cat_full[[dim, sales_col]].rename(columns={dim: "Category", sales_col: "Amount"})
            event = st.altair_chart(bar_chart(cat, "Category", "Amount", horizontal=True, select="drill", selected=cat_item),
                                    width="stretch", on_select="rerun", key=k("cat_chart", "cat"))
            dbl = event.selection.get("drill") or []
            drill = dbl[0]["Category"] if dbl else None
        else:
            st.dataframe(cat_full, hide_index=True, width="stretch",
                         on_select="rerun", selection_mode="single-row", key=k("cat_table", "cat"),
                         column_config={sales_col: st.column_config.NumberColumn(format="dollar"),
                                        units_col: st.column_config.NumberColumn(format="localized")})
        st.session_state[k("cat_names", "cat")] = cat_full[dim].tolist()
        if drill in cat_names:
            _open_return_rate(folder, dim, drill)
        if cat_item:
            if st.button(f"Open Return Rate for {cat_item} \u2192", key=k("drill_btn", "cat")):
                _open_return_rate(folder, dim, cat_item)
        else:
            st.caption(f"Click a {dim.lower()} to filter the page, double-click to open its Return Rate analysis.")

    with store_card:
        store_full = query(f"{folder}/store_breakdown.sql", **{**F, "store_id": 0})
        store_full.columns = ["StoreID", "Store", "Count", "Amount", "Latitude", "Longitude", "Type"]
        if store_view == "Visual":
            st.altair_chart(bar_chart(store_full[["Store", "Amount"]], "Store", "Amount", horizontal=True, select="filter",
                                      selected=store_name),
                            width="stretch", on_select="rerun", key=k("store_chart", "store"))
        else:
            store_map(store_full, sales_col, key=k("store_map", "store"))
        if not store_name:
            st.caption("Click a store to filter the page.")

    with month_card:
        month_flt = {**F, "month": ""}
        if month_view == "Month":
            month_df = query(f"{folder}/net_sales_per_month.sql", **month_flt)
            month_df.columns = ["Month", "Amount"]
            st.altair_chart(bar_chart(month_df, "Month", "Amount", horizontal=False, select="filter", selected=month),
                            width="stretch", on_select="rerun", key=k("month_chart", "month"))
        else:
            by_store = query(f"{folder}/net_sales_per_month_store.sql", **month_flt)
            by_store.columns = ["Month", "Store", "Amount"]
            st.altair_chart(store_line_chart(by_store, sales_col, selectable=True, selected_month=month),
                            width="stretch", on_select="rerun", key=k("month_line", "month"))
        if not month:
            st.caption("Click a month to filter the page.")


def net_sales_page():
    render("Net Sales", "net_sales", "Net Sales", "total_net_sales.sql", "units_sales.sql",
           "Net Sales", "Units Sold")


def returned_page():
    render("Returned", "sales_return", "Returned", "sales_return.sql", "units_returned.sql",
           "Sales Returns", "Units Returned")


def return_rate_page():
    dim = st.query_params.get("dim", "Product")
    item = st.query_params.get("item")
    back = RETURNED_PAGE if st.session_state.get("rr_origin") == "sales_return" else NET_SALES_PAGE
    if st.button("← Back"):
        st.switch_page(back)
    st.title(f"Return Rate · {item}" if item else "Return Rate")
    if not item:
        st.info("Pick a category or product in the Category breakdown to see its return rate.")
        return
    return_rate.render(dim, item)


NET_SALES_PAGE = st.Page(net_sales_page, title="Net Sales", url_path="net-sales", default=True)
RETURNED_PAGE = st.Page(returned_page, title="Returned", url_path="returned")
RETURN_RATE_PAGE = st.Page(return_rate_page, title="Return Rate", url_path="return-rate", visibility="hidden")

st.navigation([NET_SALES_PAGE, RETURNED_PAGE, RETURN_RATE_PAGE]).run()
