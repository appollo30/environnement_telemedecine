import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import plotly.express as px
from src.serializers import SequenceOutput, SequenceContext
from typing import List
import matplotlib.pyplot as plt


def compare_sequences(sequences : List[SequenceOutput], channel: str):
    color_map = {
            SequenceContext.MONTEE: "blue",
            SequenceContext.DESCENTE: "red",
            SequenceContext.MARCHE: "green",
            SequenceContext.APNEE: "orange",
            SequenceContext.REPOS: "gray",
    }
    
    n = len(sequences)
    descriptions = [str_shorten(seq.sequenceDescription,40) for seq in sequences]
    fig = make_subplots(rows=1, cols=n, shared_yaxes=True, subplot_titles=descriptions)
    
    for i, seq in enumerate(sequences):
        df = seq.dataframe
        fig.add_trace(px.box(df, y=channel,  color_discrete_sequence=[color_map.get(seq.sequenceContext, "tab:gray")]).data[0], row=1, col=i+1)
        
    fig.update_layout(height=400, showlegend=False, title_text=f"Comparaison des séquences pour le canal '{channel}'")
    return fig
    
    
def str_shorten(s: str, max_length: int) -> str:
    if len(s) <= max_length:
        return s
    else:
        return s[:max_length-3] + "..."
    
