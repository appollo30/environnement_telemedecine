import pandas as pd
import numpy as np
import json
from typing import List, Tuple, Dict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import butter, filtfilt

DEVICE_MAC_ADDRESS = "00:07:80:65:E0:11" # L'adresse MAC de notre capteur
NBITS = 16 # Nombre de bits utilisés pour encoder les données, ici les 3 capteurs utilisent 16 bits
CMIN_X = 26300 
CMIN_Y = 26000
CMIN_Z = 26000
CMAX_X = 39100
CMAX_Y = 38900
CMAX_Z = 39000
SAMPLING_RATE = 200 # Hz, fréquence d'échantillonnage

def parse_raw(file_content : List[str]) -> Tuple[Dict, pd.DataFrame]:
    header = file_content[1][2:]
    header_json = json.loads(header)
    sampling_rate = header_json[DEVICE_MAC_ADDRESS]["sampling rate"]
    date = header_json[DEVICE_MAC_ADDRESS]["date"]
    time = header_json[DEVICE_MAC_ADDRESS]["time"]
    
    payload = file_content[3:]
    result = []
    for line in payload:
        line_split = line.split() # On découpe chaque ligne en fonction des espaces
        # La première colonne est simplement des index de 0 à n, on l'ignore.
        # Il y a une colonne (la deuxième) qui est remplie de zéros, on l'ignore également.
        result.append({
            "THORAX" : int(line_split[2]),
            "X" : int(line_split[3]),
            "Y" : int(line_split[4])
        })
    df = pd.DataFrame(result)
    df["timestamp"] = pd.date_range(start=f"{date} {time}", periods=len(df), freq=pd.Timedelta(milliseconds=1000/sampling_rate))
    df = df[["timestamp", "THORAX", "X", "Y"]]
    #df = df.set_index("timestamp")
    
    # Fonctions de transfert, on convertit les valeurs brutes en valeurs physiques
    df["THORAX"] = df["THORAX"].apply(convert_thorax) # En pourcentage de la capacité totale
    df["X"] = df["X"].apply(lambda x: (x - CMIN_X) / (CMAX_X - CMIN_X) * 2 - 1) # En g
    df["Y"] = df["Y"].apply(lambda y: (y - CMIN_Y) / (CMAX_Y - CMIN_Y) * 2 - 1) # En g
    
    # Rajouter des filtres si besoin
    
    return header_json, df

# Traitement des données

def convert_thorax(raw_value: int) -> float:
    return (raw_value/(2**NBITS)-0.5)*100

def simple_line_plot(df : pd.DataFrame):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=["THORAX", "X", "Y"])

    fig.add_trace(go.Scatter(x=df.index, y=df["THORAX"], name="Activité respiratoire"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["X"], name="X"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Y"], name="Y"), row=3, col=1)

    fig.update_layout(height=800, showlegend=False)
    return fig

def fourier_transform_plot(df : pd.DataFrame):
    n = len(df)
    freq = np.fft.rfftfreq(n, d=1/SAMPLING_RATE)
    fft_thorax = np.abs(np.fft.rfft(df["THORAX"]))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=fft_thorax, mode='lines', name='THORAX'))
    fig.update_layout(title='Fourier Transform of THORAX', xaxis_title='Frequency (Hz)', yaxis_title='Amplitude')
    fig.update_xaxes(range=[0, 5])
    return fig

def segment_data(df : pd.DataFrame, sequences : List[Dict]) -> List[Tuple[pd.DataFrame, str]]:
    segmented_dfs = []
    for sequence in sequences:
        begin = sequence["begin"]
        end = sequence["end"]
        segmented_dfs.append((df.iloc[begin:end+1].copy(), sequence["sequenceContext"]))
    return segmented_dfs

def segment_plot(df : pd.DataFrame, sequences : List[Dict]):
    segmented_dfs = segment_data(df, sequences)
    
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=["THORAX", "X", "Y"])
    color_map = dict(zip(["MONTEE", "DESCENTE", "MARCHE", "APNEE", "REPOS"], px.colors.qualitative.Plotly))
    fig.add_trace(go.Scatter(x=df.index, y=df["THORAX"], mode='lines', line=dict(color='gray'), name="other"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["X"], mode='lines', line=dict(color='gray'), name='other'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Y"], mode='lines', line=dict(color='gray'), name='other'), row=3, col=1)
    for df, context in segmented_dfs:
        color = color_map.get(context, "gray")
        fig.add_trace(go.Scatter(x=df.index, y=df["THORAX"], mode='lines', line=dict(color=color), name=context), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["X"], mode='lines', line=dict(color=color), name=context), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Y"], mode='lines', line=dict(color=color), name=context), row=3, col=1)
    fig.update_layout(height=800, showlegend=False)
    return fig
        