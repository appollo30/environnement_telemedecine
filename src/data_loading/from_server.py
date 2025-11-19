import requests
from typing import List, Dict
from src.serializers import SessionOutput, SequenceOutput

def load_sessions_from_student(student_id: str, url: str, auth_token: str) -> List[SessionOutput]:
    """
    Charge les sessions d'un étudiant depuis un serveur distant via une requête HTTP authentifiée.

    Args:
        student_id (str): Identifiant unique de l'étudiant dont on veut charger les sessions.
        url (str): URL de base du serveur pour accéder aux données des étudiants.
        auth_token (str): Token d'authentification pour accéder aux données du serveur.

    Returns:
        List[SessionOutput]: Liste des objets SessionOutput représentant les sessions de l'étudiant.
    """
    print(f"Chargement des sessions pour l'étudiant {student_id} depuis le serveur")
    headers = {
        'Authorization': f'Basic {auth_token}'
    }

    response = requests.get(f"{url}/{student_id}", headers=headers, data={})

    sessions_json = response.json()

    payload = sessions_json.get("datasets")[0].get("sessions")
    session_ids = list(payload.keys())
    result = []
    for session_id, session_json in payload.items():
        print(session_id)
        sequences = []
        for sequence_json in session_json.get("sequences"):
            sequences.append(SequenceOutput(**sequence_json))

        session_json = {
            "studentId": student_id,
            "sessionId": session_id,
            "sequences": sequences
        }
        session = SessionOutput(**session_json)
        result.append(session)

    return result

def load_all_sessions(url: str, auth_token: str) -> Dict[str, List[SessionOutput]]:
    """
    Charge les sessions de tous les étudiants (E1 à E8) depuis un serveur distant.

    Args:
        url (str): URL de base du serveur pour accéder aux données des étudiants.
        auth_token (str): Token d'authentification pour accéder aux données du serveur.

    Returns:
        Dict[str, List[SessionOutput]]: Dictionnaire où chaque clé est un identifiant d'étudiant (ex: "E1") et chaque valeur est une liste de SessionOutput représentant les sessions de cet étudiant.
    """
    return { f"E{i}": load_sessions_from_student(f"E{i}", url, auth_token) for i in range(1,9) }
