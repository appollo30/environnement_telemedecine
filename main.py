from src.serializers import SessionInput 
from src.data_loading.from_files import load_all_sessions_from_raw_data
from src.data_writing.to_files import save_all_session_inputs_to_json
from src.data_writing.to_server import post_all_session_inputs_to_server
import os
from dotenv import load_dotenv
from typing import List        

if __name__ == "__main__":
    load_dotenv()
    url = os.getenv("SERVER_URL")
    auth_token = os.getenv("BASIC_AUTH") # ATTENTION A BIEN REMPLACER LA VALEUR DANS LE FICHIER .env
    
    input_directory = "raw_data/Leo"
    student_name = "Leo"
    
    sessions : List[SessionInput] = load_all_sessions_from_raw_data(input_directory=input_directory)
    save_all_session_inputs_to_json(sessions=sessions, student_name=student_name)
    post_all_session_inputs_to_server(sessions=sessions, url=url, auth_token=auth_token)
    