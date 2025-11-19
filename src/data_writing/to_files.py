import os
from typing import List, Dict
from src.serializers import SessionInput
import json

def save_session_input_to_json(session_input: SessionInput, student_name: str) -> None:
    student_path = os.path.join("payload_data", student_name)
    
    for sequence in session_input.sequences:
        output_path = os.path.join(student_path, f"{session_input.sessionId}-{sequence.sequenceId}.json")
        sequence_start_datetime = sequence.sequenceStartDateTime
        sequence_json = sequence.model_dump(mode="json")
        sequence_json["sequenceStartDateTime"] = sequence_start_datetime.strftime("%Y-%m-%d %H:%M:%S") # Conversion en str en format datetime mysql
        with open(output_path, "w") as f:
            json.dump(sequence_json, f, ensure_ascii=False, indent=4)

def save_all_session_inputs_to_json(sessions : List[SessionInput], student_name: str):
    for session in sessions:
        print(f"Enregistrement des fichiers JSON pour la session {session.sessionId}")
        save_session_input_to_json(session_input=session, student_name=student_name)
        
def save_all_session_outputs_to_json(all_sessions : Dict[str, List[SessionInput]]) -> None:
    
    for student_id, sessions in all_sessions.items():
        student_path = os.path.join("student_data", student_id)
        os.makedirs(student_path, exist_ok=True)
        for session in sessions:
            output_path = os.path.join(student_path, f"{session.sessionId}.json")
            with open(output_path, "w") as f:
                json.dump(session.model_dump(mode="json"), f, ensure_ascii=False, indent=4)