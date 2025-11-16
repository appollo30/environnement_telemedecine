from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from enum import Enum
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# -----------------
# Sequences

class SequenceContext(str, Enum):
    """
    Enumération des contextes possibles pour une séquence de données.
    """
    MONTEE = "MONTEE"
    DESCENTE = "DESCENTE"
    MARCHE = "MARCHE"
    APNEE = "APNEE"
    REPOS = "REPOS"

class SequenceOutput(BaseModel):
    """
    Représente une séquence de données telle que définie dans le format JSON de l'API.
    """
    deviceId: str
    sessionId: str
    sequenceId: int
    sequenceStartDateTime: datetime
    sequenceContext: SequenceContext
    sequenceDescription: str
    sequenceStructure: list[str]
    sequenceSamplingRate: int
    sequenceResolution: int
    data: list[list[float | int]]
    
    @property
    def dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(self.data, columns=self.sequenceStructure)
        df["timestamp"] = pd.date_range(start=self.sequenceStartDateTime, periods=len(df), freq=f"{int(1000/self.sequenceSamplingRate)}ms")
        df = df[["timestamp", "RESP_THORAX", "ACC_HORIZONTAL", "ACC_VERTICAL"]]
        
        return df
    
    def simple_line_plot(self, timestamp=False):
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=["Activité respiratoire (THORAX)", "Accélération horizontale (X)", "Accélération verticale (Y)"])
        
        if timestamp:
            x = self.dataframe["timestamp"]
        else:
            x = self.dataframe.index
        
        fig.add_trace(go.Scatter(x=x, y=self.dataframe["RESP_THORAX"], name="Activité respiratoire"), row=1, col=1)
        fig.add_trace(go.Scatter(x=x, y=self.dataframe["ACC_HORIZONTAL"], name="X"), row=2, col=1)
        fig.add_trace(go.Scatter(x=x, y=self.dataframe["ACC_VERTICAL"], name="Y"), row=3, col=1)

        fig.update_layout(height=800, showlegend=False)
        return fig

    def fourier_transform_plot(self, channel="RESP_THORAX"):
        n = len(self.dataframe)
        freq = np.fft.rfftfreq(n, d=1/self.sequenceSamplingRate)
        # On normalise le signal en enlevant la moyenne, pour éviter un pic à la fréquence 0
        channel_normalized = self.dataframe[channel] - np.mean(self.dataframe[channel])
        fft = np.abs(np.fft.rfft(channel_normalized))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=freq, y=fft, mode='lines', name=channel))
        fig.update_layout(title=f'Transformée de fourier du signal {channel}', xaxis_title='Fréquence (Hz)', yaxis_title='Amplitude')
        fig.update_xaxes(range=[0, 5])
        return fig
    
class SequenceInput(SequenceOutput):
    studentId: str # studentId privé, pour l'envoi au serveur
    
# -----------------
# Sessions

class SessionHeader(BaseModel):
    sampling_rate: int
    start_datetime : datetime
    resolution : int
    
class SequenceMetadata(BaseModel):
    sequenceId: int
    begin : int
    end : int
    sequenceContext: SequenceContext
    sequenceDescription: str | None = None

class SessionMetadata(BaseModel):
    studentId: str
    sessionDescription: str
    sessionId: str
    sequences: list[SequenceMetadata]
    
class SessionInput(BaseModel):
    studentId: str # studentId privé, pour l'envoi au serveur
    sessionId: str
    sequences: list[SequenceInput]
    
class SessionOutput(BaseModel):
    studentId: str # studentId public, pour la lecture des données depuis le serveur
    sessionId: str
    sequences: list[SequenceOutput]
    
