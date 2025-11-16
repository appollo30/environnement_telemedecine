import pandas as pd
import json
from typing import List, Dict
from src.serializers import SequenceInput, SessionHeader, SessionMetadata, SessionInput
from datetime import datetime
import os
from glob import glob

DEVICE_MAC_ADDRESS = "00:07:80:65:E0:11" # L'adresse MAC de notre capteur
NBITS = 16 # Nombre de bits utilisés pour encoder les données, ici les 3 capteurs utilisent une résolution de 16 bits
CMIN_X = 26300 
CMIN_Y = 26000
CMIN_Z = 26000
CMAX_X = 39100
CMAX_Y = 38900
CMAX_Z = 39000

def load_header(txt_file_raw_content : List[str]) -> SessionHeader:
    header = txt_file_raw_content[1][2:]
    header_json = json.loads(header).get(DEVICE_MAC_ADDRESS)
    return SessionHeader(
        sampling_rate=header_json.get("sampling rate"),
        start_datetime=datetime.strptime(
            f"{header_json.get('date')} {header_json.get('time')}",
            "%Y-%m-%d %H:%M:%S.%f"
        ),
        resolution=header_json.get("resolution")[0]
    ) 

def generate_session_df(txt_file_raw_content : List[str]) -> pd.DataFrame:
    data = txt_file_raw_content[3:] 
    result = []
    for line in data:
        line_split = line.split() # On découpe chaque ligne en fonction des espaces
        # La deuxième colonne est remplie de zéros, donc on l'ignore.
        result.append({
            "INDEX" : int(line_split[0]),
            "RESP_THORAX" : int(line_split[2]),
            "ACC_HORIZONTAL" : int(line_split[3]),
            "ACC_VERTICAL" : int(line_split[4])
        })
    df = pd.DataFrame(result) # Il s'agit de la Dataframe brute de la session, 
    # Il faudra la segmenter en plusieurs Dataframes de séquences plus tard.
    
    # Fonctions de transfert, on convertit les valeurs brutes en valeurs physiques
    df["RESP_THORAX"] = df["RESP_THORAX"].apply(convert_thorax) # En pourcentage de la capacité totale
    df["ACC_HORIZONTAL"] = df["ACC_HORIZONTAL"].apply(lambda x: (x - CMIN_X) / (CMAX_X - CMIN_X) * 2 - 1) # En g
    df["ACC_VERTICAL"] = df["ACC_VERTICAL"].apply(lambda y: (y - CMIN_Y) / (CMAX_Y - CMIN_Y) * 2 - 1) # En g
    
    # Rajouter des filtres si besoin
    
    return df

def convert_thorax(raw_value: int) -> float:
    return (raw_value/(2**NBITS)-0.5)*100

def segment_data(session_df : pd.DataFrame, metadata = SessionMetadata) -> List[pd.DataFrame]:
    sequences = metadata.sequences
    df = session_df.copy()
    segmented_dfs = []
    for sequence in sequences:
        begin = sequence.begin
        end = sequence.end
        sequence_df = df.iloc[begin:end+1].copy().reset_index(drop=True)
        segmented_dfs.append(sequence_df)
    return segmented_dfs

def to_session(segmented_dfs : List[pd.DataFrame], metadata : SessionMetadata, header : SessionHeader) -> SessionInput:
    device_id = DEVICE_MAC_ADDRESS
    student_id = metadata.studentId
    session_id = metadata.sessionId
    session_description = metadata.sessionDescription
    
    sequence_structure = [
        "INDEX",
        "RESP_THORAX",
        "ACC_HORIZONTAL",
        "ACC_VERTICAL"
    ]
    
    sequence_sampling_rate = header.sampling_rate
    sequence_resolution = header.resolution
    
    sequences = []
    
    for sequence_df, sequence_metadata in zip(segmented_dfs, metadata.sequences):
        sequence_id = sequence_metadata.sequenceId
        sequence_start_datetime = header.start_datetime + pd.Timedelta(seconds=sequence_metadata.begin / sequence_sampling_rate)
        sequence_start_datetime_str = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        sequence_context = sequence_metadata.sequenceContext
        if sequence_metadata.sequenceDescription:
            sequence_description = f"{session_description}, {sequence_metadata.sequenceDescription}"
        else:
            sequence_description = session_description
        
        # Transformations sur la DataFrame
        sequence_df = sequence_df.reset_index(drop=True) # On reset l'index (l'index est conservé lors 
        # du séquençage, donc les séquences ne commencent pas forcément à 0 par défaut)
        sequence_df["INDEX"] = sequence_df.index.astype(int) # On ajoute une colonne d'index
        data = sequence_df.values.tolist()
        
        sequence_json = {
            "deviceId": device_id,
            "studentId": student_id, # studentId privé, pour l'envoi au serveur
            "sessionId": session_id,
            "sequenceId": sequence_id,
            "sequenceStartDateTime": sequence_start_datetime_str,
            "sequenceContext": sequence_context,
            "sequenceDescription": sequence_description,
            "sequenceStructure" : sequence_structure,
            "sequenceSamplingRate": sequence_sampling_rate,
            "sequenceResolution": sequence_resolution,
            "data" : data
        }
        sequences.append(SequenceInput(**sequence_json))
    session = SessionInput(studentId=student_id, sessionId=session_id, sequences=sequences)
    return session
    

def load_session(metadata_json : Dict, txt_file_raw_content : List[str]) -> SessionInput:
    # CHARGEMNENT DES METADONNEES ET DU HEADER
    
    metadata = SessionMetadata(**metadata_json)
    header = load_header(txt_file_raw_content)
    
    # CHARGEMENT DES DONNEES
    
    session_df = generate_session_df(txt_file_raw_content)
    # Il s'agit de la Dataframe brute de la session, 
    # Il faudra la segmenter en plusieurs Dataframes de séquences plus tard.
    
    
    # SEGMENTATION DES DONNEES
    
    segmented_dfs = segment_data(session_df, metadata) 
    # Liste de DataFrames, une par séquence.
    
    # CREATION DE L'OBJET SESSION
    
    session = to_session(segmented_dfs, metadata, header)
    
    return session

# CHARGEMENT DE TOUTES LES SESSIONS A PARTIR D'UN REPERTOIRE DE DONNEES BRUTES    

def load_all_sessions_from_raw_data(input_directory: str) -> List[SessionInput]:
    if not os.path.isdir(input_directory):
        raise FileNotFoundError(f"Le chemin {input_directory} que vous avez renseigné n'existe pas ou n'est pas un répertoire")
    
    session_dirs = [d for d in glob(os.path.join(input_directory, "*")) if os.path.isdir(d)]
    sessions = []
    for session_path in session_dirs:
        try:
            recording_file_path = glob(os.path.join(session_path, "*.txt"))[0]
            metadata_file_path = glob(os.path.join(session_path, "*.json"))[0]
        except IndexError:
            print(f"Le répertoire {session_path} devrait contenir EXCLUSIVEMENT un fichier .txt et un fichier .json. Ignoré.")
            continue
        
        print(f"Traitement de la session du répertoire : {session_path}")
        
        with open(recording_file_path, 'r') as f:
            txt_file_raw_content = f.readlines()
        
        with open(metadata_file_path, 'r') as meta_file:
            metadata_json = json.load(meta_file)
        
        session = load_session(metadata_json, txt_file_raw_content)
        sessions.append(session)
    
    return sessions