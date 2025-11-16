from src.serializers import SessionInput
import json
import os
from typing import Union
import requests
from typing import List

def post_session_input_to_server(session_input: SessionInput, url: str, auth_token: str) -> None:
    headers = {
        'Authorization': f'Basic {auth_token}'
    }
    
    for sequence in session_input.sequences:
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S") # Conversion en str en format datetime mysql
        form_data = {'dataset': json.dumps(sequence_json, ensure_ascii=False)}
        response = requests.post(url, headers=headers, data=form_data)

        print(json.dumps(response.json(), ensure_ascii=False, indent=4))
        
        
def post_all_session_inputs_to_server(sessions : List[SessionInput], url: str, auth_token: str) -> None:
    for session in sessions:
        print(f"Envoi de la session {session.sessionId} au serveur")
        post_session_input_to_server(session_input=session, url=url, auth_token=auth_token)