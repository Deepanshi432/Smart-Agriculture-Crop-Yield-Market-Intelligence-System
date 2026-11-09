"""STEP 7 - Interactive Plotly Dash dashboard.
Run:  python dashboard/app.py   ->  open http://127.0.0.1:8050
Reads data/processed/*.csv (run scripts 01-04 first).
"""
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"
crop = pd.read_csv(PROCESSED / "merged_yield_data.csv")
mandi = pd.read_csv(PROCESSED / "cleaned_mandi_prices.csv")

crops = sorted(crop["crop"].unique())
states = ["All"] + sorted(crop["state"].unique())
seasons = ["All"] + sorted(crop["season"].unique())
y0, y1 = int(crop["year"].min()), int(crop["year"].max())

app = Dash(__name__)
app.title = "Smart Agriculture Dashboard"

box = {"width": "22%", "display": "inline-block", "padding": "6px"}
app.layout = html.Div(style={"fontFamily": "Arial", "padding": "16px"}, children=[
    html.H2("Smart Agriculture: Crop Yield & Market Intelligence"),
    html.Div([
        html.Div([html.Label("Crop"), dcc.Dropdown(crops, "Rice", id="crop", clearable=False)], style=box),
        html.Div([html.Label("State"), dcc.Dropdown(states, "All", id="state", clearable=False)], style=box),
        html.Div([html.Label("Season"), dcc.Dropdown(seasons, "All", id="season", clearable=False)], style=box),
        html.Div([html.Label("Years"), dcc.RangeSlider(y0, y1, 1, value=[y0, y1], id="years",
                  marks={y: str(y) for y in range(y0, y1 + 1, 5)})], style={"width": "30%", "display": "inline-block"}),
    ]),
    html.Div(id="kpis", style={"display": "flex", "gap": "24px", "margin": "12px 0"}),
    html.Div([dcc.Graph(id="trend", style={"width": "50%", "display": "inline-block"}),
              dcc.Graph(id="districts", style={"width": "50%", "display": "inline-block"})]),
    html.Div([dcc.Graph(id="rain", style={"width": "50%", "display": "inline-block"}),
              dcc.Graph(id="price", style={"width": "50%", "display": "inline-block"})]),
])


def filtered(crop_name, state, season, years):
    d = crop[(crop["crop"] == crop_name) & crop["year"].between(*years)]
    if state != "All":
        d = d[d["state"] == state]
    if season != "All":
        d = d[d["season"] == season]
    return d


def kpi(title, value):
    return html.Div([html.Div(title, style={"fontSize": "12px", "color": "#666"}),
                     html.Div(value, style={"fontSize": "22px", "fontWeight": "bold"})],
                    style={"border": "1px solid #ddd", "borderRadius": "8px", "padding": "10px 18px"})


@app.callback(Output("kpis", "children"), Output("trend", "figure"), Output("districts", "figure"),
              Output("rain", "figure"), Output("price", "figure"),
              Input("crop", "value"), Input("state", "value"), Input("season", "value"), Input("years", "value"))
def update(crop_name, state, season, years):
    d = filtered(crop_name, state, season, years)
    unit = d["yield_unit_note"].iloc[0] if len(d) else ""
    kpis = [kpi("Records", f"{len(d):,}"),
            kpi(f"Avg yield ({unit})", f"{d['yield'].mean():.2f}" if len(d) else "-"),
            kpi("Total production", f"{d['production'].sum():,.0f}"),
            kpi("Districts", f"{d['district'].nunique():,}")]

    t = d.groupby("year")["yield"].mean().reset_index()
    trend = px.line(t, x="year", y="yield", markers=True, title=f"{crop_name}: average yield by year")

    top = d.groupby(["state", "district"])["yield"].mean().nlargest(10).reset_index()
    top["label"] = top["district"] + " (" + top["state"] + ")"
    districts = px.bar(top, x="yield", y="label", orientation="h", title="Top 10 districts by yield")
    districts.update_layout(yaxis={"categoryorder": "total ascending"})

    r = d.groupby(["state", "year"]).agg(y=("yield", "mean"), rain=("season_rainfall", "mean")).reset_index()
    rain = px.scatter(r, x="rain", y="y", color="state", opacity=0.6, title="Season rainfall (mm) vs yield",
                      labels={"rain": "Season rainfall (mm)", "y": "Yield"})

    m = mandi[mandi["commodity"].str.contains(crop_name.split("(")[0], case=False, regex=False)]
    if len(m):
        p = m.groupby("state")["modal_price"].mean().nlargest(10).reset_index()
        price = px.bar(p, x="state", y="modal_price", title=f"Mandi price today: {crop_name} (Rs/quintal)")
    else:
        price = px.bar(title=f"No mandi price found for {crop_name} today")
    return kpis, trend, districts, rain, price


if __name__ == "__main__":
    app.run(debug=False, port=8050)
