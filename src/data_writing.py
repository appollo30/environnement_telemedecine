from src.serializers import SessionInput, SessionOutput
import json
import os
from typing import Union
import requests
from typing import List

def save_session_input_to_json(session_input: SessionInput, student_name: str):
    student_path = os.path.join("payload_data", student_name)
    
    for sequence in session_input.sequences:
        output_path = os.path.join(student_path, f"{session_input.sessionId}-{sequence.sequenceId}.json")
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S") # Conversion en str en format datetime mysql
        with open(output_path, "w") as f:
            json.dump(sequence_json, f, ensure_ascii=False, indent=4)
            
def post_session_input_to_server(session_input: SessionInput, url: str, auth_token: str) -> Union[dict, None]:
    headers = {
        'Authorization': f'Basic {auth_token}', # ATTENTION A BIEN REMPLACER LA VALEUR DANS LE FICHIER .env
    }
    
    for sequence in session_input.sequences:
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S") # Conversion en str en format datetime mysql
        form_data = {'dataset': json.dumps(sequence_json, ensure_ascii=False)}
        response = requests.post(url, headers=headers, data=form_data)

        print(json.dumps(response.json(), ensure_ascii=False, indent=4))



def save_all_sessions_to_json(sessions : List[SessionInput], student_name: str):
    for session in sessions:
        print(f"Enregistrement des fichiers JSON pour la session {session.sessionId}")
        save_session_input_to_json(session_input=session, student_name=student_name)

def post_all_sessions_to_server(sessions : List[SessionInput], url: str, auth_token: str):
    for session in sessions:
        print(f"Envoi de la session {session.sessionId} au serveur")
        post_session_input_to_server(session_input=session, url=url, auth_token=auth_token)