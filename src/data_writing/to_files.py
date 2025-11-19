import os
from typing import List, Dict
from src.serializers import SessionInput
import json

def save_session_input_to_json(session_input: SessionInput, student_name: str) -> None:
    """
    Enregistre chaque séquence d'une session au format JSON dans un répertoire dédié à l'étudiant.

    Args:
        session_input (SessionInput): Objet SessionInput contenant les données de la session à enregistrer.
        student_name (str): Nom de l'étudiant, utilisé pour créer le chemin de stockage.
    """
    student_path = os.path.join("payload_data", student_name)

    for sequence in session_input.sequences:
        output_path = os.path.join(student_path, f"{session_input.sessionId}-{sequence.sequenceId}.json")
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S")  # Conversion en str en format datetime mysql
        with open(output_path, "w") as f:
            json.dump(sequence_json, f, ensure_ascii=False, indent=4)

def save_all_session_inputs_to_json(sessions: List[SessionInput], student_name: str) -> None:
    """
    Enregistre toutes les sessions d'un étudiant au format JSON.

    Args:
        sessions (List[SessionInput]): Liste des objets SessionInput à enregistrer.
        student_name (str): Nom de l'étudiant, utilisé pour créer le chemin de stockage.
    """
    for session in sessions:
        print(f"Enregistrement des fichiers JSON pour la session {session.sessionId}")
        save_session_input_to_json(session_input=session, student_name=student_name)

def save_all_session_outputs_to_json(all_sessions: Dict[str, List[SessionInput]]) -> None:
    """
    Enregistre toutes les sessions de tous les étudiants au format JSON dans des répertoires dédiés.

    Args:
        all_sessions (Dict[str, List[SessionInput]]): Dictionnaire où chaque clé est un identifiant d'étudiant et chaque valeur est une liste de SessionInput à enregistrer.
    """
    for student_id, sessions in all_sessions.items():
        student_path = os.path.join("student_data", student_id)
        os.makedirs(student_path, exist_ok=True)
        for session in sessions:
            output_path_json = os.path.join(student_path, f"{session.sessionId}.json")
            output_path_jpeg = os.path.join(student_path, f"{session.sessionId}.jpeg")
            with open(output_path_json, "w") as f:
                json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=4)
                try:
                    plot = session.plot(channel="RESP_THORAX", timestamp=True)
                    plot.savefig(output_path_jpeg)
                except Exception as e:
                    print(f"Erreur lors de la génération du plot pour la session {session.sessionId} de l'étudiant {student_id}: {e}")
                
