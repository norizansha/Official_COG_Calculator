import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import io

# KONFIGURASI HALAMAN WEB
st.set_page_config(page_title="Steel Structure COG", layout="wide")
st.title("🏗️ Steel Structure: COG Analyzer")

# 1. LINK DATA GOOGLE SHEETS
url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vT8UD-U2BQwZsPJ0vBQAj5eMy3ioU_5fmpNjzPE71KQ0Wk8dQlKTahPpvOuJzp1SVUxLWuWRluyDdNn/pub?output=csv'

@st.cache_data(ttl=5) # Refresh data setiap 5 saat
def load_data():
    try:
        response = requests.get(url)
        df = pd.read_csv(io.BytesIO(response.content))
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return None

df = load_data()

if df is not None:
    # MENCARI 'AO' SEBAGAI TITIK RUJUKAN (0,0)
    ao_data = df[df['Item'].str.strip() == 'AO']
    if ao_data.empty:
        orig_ref_x, orig_ref_y = df.iloc[0]['X'], df.iloc[0]['Y']
    else:
        orig_ref_x = ao_data['X'].values[0]
        orig_ref_y = ao_data['Y'].values[0]

    # Shift koordinat
    df['X_rel'] = df['X'] - orig_ref_x
    df['Y_rel'] = df['Y'] - orig_ref_y

    # PENGIRAAN COG
    total_w = df['Weight'].sum()
    cog_x = (df['Weight'] * df['X']).sum() / total_w
    cog_y = (df['Weight'] * df['Y']).sum() / total_w
    cog_z = (df['Weight'] * df['Z']).sum() / total_w

    cog_x_rel = cog_x - orig_ref_x
    cog_y_rel = cog_y - orig_ref_y

    # LUKIS GRAF
    fig = go.Figure()

    # Boundary: O -> AO -> O1 -> O2 -> O3 -> O
    boundary_sequence = ['O', 'AO', 'O1', 'O2', 'O3', 'O']
    b_x, b_y = [], []
    for b_node in boundary_sequence:
        point = df[df['Item'].str.strip() == b_node]
        if not point.empty:
            b_x.append(point['X_rel'].values[0])
            b_y.append(point['Y_rel'].values[0])

    if b_x:
        fig.add_trace(go.Scatter(x=b_x, y=b_y, mode='lines+markers',
                                 line=dict(color='black', width=3), name='Steel Boundary'))

    # Plot Nodes
    for item in df['Item'].unique():
        mask = df['Item'] == item
        lbl = item.strip()
        fig.add_trace(go.Scatter(x=df[mask]['X_rel'], y=df[mask]['Y_rel'],
                                 mode='markers+text', text=lbl, textposition="top right",
                                 marker=dict(symbol='x', size=12), name=f"Node {lbl}"))

    # Plot COG (Merah)
    fig.add_trace(go.Scatter(x=[cog_x_rel], y=[cog_y_rel], mode='markers+text',
                             marker=dict(symbol='x', size=20, color='red', line=dict(width=3)),
                             text=["<b>FINAL COG</b>"], textposition="bottom center", name='COG'))

    fig.update_layout(xaxis=dict(title="X (m)"), yaxis=dict(title="Y (m)", scaleanchor="x"), 
                      template='plotly_white', height=700)

    # Paparkan di Web
    st.plotly_chart(fig, use_container_width=True)

    # Paparkan Keputusan (Metrik)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Weight", f"{total_w:.3f} T")
    c2.metric("COG X", f"{cog_x:.3f} m")
    c3.metric("COG Y", f"{cog_y:.3f} m")
    c4.metric("COG Z", f"{cog_z:.3f} m")
    
    st.write("### Data Table", df[['Item', 'X', 'Y', 'Z', 'Weight']])
else:
    st.error("Gagal ambil data. Sila pastikan Google Sheets anda 'Published to Web'.")
