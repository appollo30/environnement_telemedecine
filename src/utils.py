import pandas as pd
import numpy as np
import json
from typing import List, Tuple, Dict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import butter, filtfilt

DEVICE_MAC_ADDRESS = "00:07:80:65:E0:11" # L'adresse MAC de notre capteur

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
    df = df.set_index("timestamp")
    
    # Filtre butterworth :
    # df = butterworth_filter_thorax(df)
    
    return header_json, df

def simple_line_plot(df : pd.DataFrame):
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=["THORAX", "X", "Y"])

    fig.add_trace(go.Scatter(x=df.index, y=df["THORAX"], name="Activité respiratoire"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["X"], name="X"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Y"], name="Y"), row=3, col=1)

    fig.update_layout(height=800, showlegend=False)
    return fig

def fourier_transform_plot(df : pd.DataFrame):
    n = len(df)
    sampling_rate = df.shape[0] / (df.index[-1] - df.index[0]).total_seconds()
    freq = np.fft.rfftfreq(n, d=1/sampling_rate)
    fft_thorax = np.abs(np.fft.rfft(df["THORAX"]))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=fft_thorax, mode='lines', name='THORAX'))
    fig.update_layout(title='Fourier Transform of THORAX', xaxis_title='Frequency (Hz)', yaxis_title='Amplitude')
    fig.update_xaxes(range=[0, 1])
    return fig

def butterworth_filter_thorax(df: pd.DataFrame, lowcut=0.05, highcut=0.8, order=4) -> pd.DataFrame:
    # Calculate sampling rate from DataFrame index
    sampling_rate = df.shape[0] / (df.index[-1] - df.index[0]).total_seconds()
    nyq = 0.5 * sampling_rate
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    filtered = filtfilt(b, a, df["THORAX"].values)
    df_filtered = df.copy()
    df_filtered["THORAX"] = filtered
    return df_filtered