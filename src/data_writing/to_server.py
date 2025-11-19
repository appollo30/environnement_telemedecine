from src.serializers import SessionInput
import json
import os
from typing import Union, List
import requests

def post_session_input_to_server(session_input: SessionInput, url: str, auth_token: str) -> None:
    """
    Envoie les séquences d'une session au serveur via une requête HTTP POST authentifiée.

    Args:
        session_input (SessionInput): Objet SessionInput contenant les données de la session à envoyer.
        url (str): URL du serveur où envoyer les données.
        auth_token (str): Token d'authentification pour accéder au serveur.
    """
    headers = {
        'Authorization': f'Basic {auth_token}'
    }

    for sequence in session_input.sequences:
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S")  # Conversion en str en format datetime MySQL
        form_data = {'dataset': json.dumps(sequence_json, ensure_ascii=False)}
        response = requests.post(url, headers=headers, data=form_data)
        print(json.dumps(response.json(), ensure_ascii=False, indent=4))

def post_all_session_inputs_to_server(sessions: List[SessionInput], url: str, auth_token: str) -> None:
    """
    Envoie toutes les sessions d'une liste au serveur via une requête HTTP POST authentifiée.

    Args:
        sessions (List[SessionInput]): Liste des objets SessionInput à envoyer.
        url (str): URL du serveur où envoyer les données.
        auth_token (str): Token d'authentification pour accéder au serveur.
    """
    for session in sessions:
        print(f"Envoi de la session {session.sessionId} au serveur")
        post_session_input_to_server(session_input=session, url=url, auth_token=auth_token)
