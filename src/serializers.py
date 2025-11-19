from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from enum import Enum
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

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
        df["ACC"] = np.sqrt(df["ACC_HORIZONTAL"]**2 + df["ACC_VERTICAL"]**2)
        df["sequenceContext"] = self.sequenceContext.value
        df = df[["timestamp", "RESP_THORAX", "ACC_HORIZONTAL", "ACC_VERTICAL", "ACC", "sequenceContext"]]
        
        return df
    
    def simple_line_plot(self,channel, timestamp=False):
        fig = go.Figure()
        df = self.dataframe
        if timestamp:
            x = df["timestamp"]
            xlabel = "Time"
        else:
            x = df.index
            xlabel = "Sample index"
        fig.add_trace(go.Scatter(x=x, y=df[channel], mode='lines', name=channel))
        fig.update_layout(title=f'Signal {channel}', xaxis_title=xlabel, yaxis_title=channel)
        return fig
    
    def simple_line_plot_with_peaks(self, channel="RESP_THORAX", prominence=8,timestamp=False):
        fig = go.Figure()
        df = self.dataframe

        if timestamp:
            x = df["timestamp"]
            xlabel = "Time"
        else:
            x = df.index
            xlabel = "Sample index"

        # Plot the original signal
        fig.add_trace(go.Scatter(x=x, y=df[channel], mode='lines', name=channel))

        # Find peaks
        peaks, _ = find_peaks(df[channel], prominence=prominence)

        # Plot the peaks
        fig.add_trace(go.Scatter(
            x=x[peaks],
            y=df[channel].iloc[peaks],
            mode='markers',
            marker=dict(color='red', size=8),
            name='Peaks'
        ))

        fig.update_layout(
            title=f'Signal {channel} with Peaks',
            xaxis_title=xlabel,
            yaxis_title=channel
        )

        return fig
    
    def get_number_of_peaks(self, channel="RESP_THORAX", prominence=8) -> int:
        df = self.dataframe
        peaks, _ = find_peaks(df[channel], prominence=prominence)
        return len(peaks)

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
    
    def local_average_plot(self, channel="RESP_THORAX", window_size_seconds=5):
        window_size_samples = int(window_size_seconds * self.sequenceSamplingRate)
        df = self.dataframe.copy()
        df[f'{channel}_local_avg'] = df[channel].rolling(window=window_size_samples, center=True).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df[channel], mode='lines', name=channel, opacity=0.4))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df[f'{channel}_local_avg'], mode='lines', name=f'{channel} (moyenne locale {window_size_seconds}s)'))
        fig.update_layout(title=f'Signal {channel} avec moyenne locale', xaxis_title='Temps', yaxis_title=channel)
        return fig
    
class SequenceInput(SequenceOutput):
    studentId: str # studentId privé, pour l'envoi au serveur
    sessionId: str
    
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
    
    def get_descriptions(self) -> list[str]:
        return [seq.sequenceDescription for seq in self.sequences]
    
    def plot(self, channel, timestamp=False):

        color_map = {
            SequenceContext.MONTEE: "tab:blue",
            SequenceContext.DESCENTE: "tab:red",
            SequenceContext.MARCHE: "tab:green",
            SequenceContext.APNEE: "tab:orange",
            SequenceContext.REPOS: "tab:gray",
        }

        fig, ax = plt.subplots(figsize=(12, 5))
        used_labels = set()

        cumulative_samples = 0
        cumulative_time = 0.0  # in seconds
        
        for seq in self.sequences:
            df = seq.dataframe


            n = len(df)
            sr = seq.sequenceSamplingRate

            if timestamp:
                # Use concatenated time axis in seconds (each sequence placed after the previous)
                x = np.arange(n) / sr + cumulative_time
                cumulative_time += n / sr
                xlabel = "Time (s, concatenated sequences)"
            else:
                # Use concatenated sample index
                x = np.arange(cumulative_samples, cumulative_samples + n)
                cumulative_samples += n
                xlabel = "Sample index (concatenated sequences)"

            color = color_map.get(seq.sequenceContext, "tab:gray")
            label = seq.sequenceContext.value if seq.sequenceContext not in used_labels else None
            if label:
                used_labels.add(seq.sequenceContext)
            ax.plot(x, df[channel], color=color, label=label, linewidth=1)

        ax.set_title(f"{channel} — sequences concatenées")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(channel)
        ax.grid(True)
        if used_labels:
            ax.legend(title="Contexte de séquence")
        fig.tight_layout()
        return fig


