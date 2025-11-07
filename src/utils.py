import pandas as pd
import numpy as np
import json
from typing import List, Tuple, Dict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        
def session_to_json(df : pd.DataFrame, header_json : Dict, metadata : Dict) -> List[Dict]:
    """
    Prend en entrée 3 paramètres :
      - la DataFrame de la session, avec des colonnes pour le mouvement en X et 
        en Y, la respiration thoracique, et avec un index incrémenté de 1.
      - le header en format json, qui se trouve au début du fichier txt de la session
      - les métadonnées en format json (pour le séquencement)
    Retourne une liste de json, qui désignent chacun le request body qui sera envoyé 
    pour chaque séquence.      
    """
    result = list()
    df_copy = df.copy()
    
    sequences = metadata["sequences"]
    segmented_dfs = segment_data(df_copy, sequences)
    
    device_id = DEVICE_MAC_ADDRESS
    student_id = metadata["studentId"]
    session_id = metadata["sessionId"]
    session_description = metadata["sessionDescription"]
    
    sequence_structure = [
        "INDEX",
        "RESP_THORAX",
        "ACC_HORIZONTAL",
        "ACC_VERTICAL"
    ]
    sequence_sampling_rate = header_json[DEVICE_MAC_ADDRESS]["sampling rate"]
    sequence_resolution = header_json[DEVICE_MAC_ADDRESS]["resolution"][0]
    
    for sequence_df, sequence in zip(segmented_dfs, sequences):
        sequence_df = sequence_df[0]
        sequence_id = sequence["sequenceId"]
        sequence_start_datetime = sequence_df["timestamp"].iloc[0].strftime("%Y-%m-%d %H:%M:%S")
        sequence_context = sequence["sequenceContext"]
        if sequence.get("sequenceDescription"):
            sequence_description = f"{session_description}, {sequence.get("sequenceDescription")}"
        else:
            sequence_description = session_description
        
        # Transformations sur la DataFrame
        sequence_df = sequence_df.reset_index(drop=True) # On reset l'index (l'index est conservé lors 
        # du séquençage, donc les séquences ne commencent pas forcément à 0 par défaut)
        sequence_df["INDEX"] = sequence_df.index.astype(int) # On ajoute une colonne d'index
        sequence_df = sequence_df[["INDEX","THORAX","X","Y"]] # On supprime la colonne "timestamp"
        data = sequence_df.values.tolist()
        
        sequence_json = {
            "deviceId": device_id,
            "studentId": student_id,
            "sessionId": session_id,
            "sequenceId": sequence_id,
            "sequenceStartDateTime": sequence_start_datetime,
            "sequenceContext": sequence_context,
            "sequenceDescription": sequence_description,
            "sequenceStructure" : sequence_structure,
            "sequenceSamplingRate": sequence_sampling_rate,
            "sequenceResolution": sequence_resolution,
            "data" : data
        }
        result.append(sequence_json)
    return result
