import requests
from typing import List, Dict
from src.serializers import SessionOutput, SequenceOutput

def load_sessions_from_student(student_id: str, url: str, auth_token: str) -> List[SessionOutput]:
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
    return { f"E{i}": load_sessions_from_student(f"E{i}", url, auth_token) for i in range(1,9)}