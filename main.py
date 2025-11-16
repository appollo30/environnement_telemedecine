import argparse
import os
from src.data_loading import load_session
from src.data_writing import save_session_input_to_json, post_session_input_to_server
import json
from glob import glob
import requests
from dotenv import load_dotenv

if __name__ == "__main__":
    
    # Chargement des variables d'environnement
    load_dotenv()
    url = os.getenv("SERVER_URL")
    auth_token = os.getenv("BASIC_AUTH")
    
    # Parsing des arguments
    parser = argparse.ArgumentParser(description="Outil pour transformer des sessions en données traitées.")
    parser.add_argument("fichier", help="Chemin du repertoire à analyser")
    
    # Parsing du chemin d'accès, pour l'exécution il suffit de faire "python main.py <chemin_vers_le_répertoire.txt>"
    # Exemple : python main.py raw_data/Leo/S3
    args = parser.parse_args()
    session_path = args.fichier
    if not os.path.isdir(session_path):
        raise FileNotFoundError(f"Le chemin {session_path} que vous avez renseigné n'existe pas ou n'est pas un répertoire")
    try :
        recording_file_path = glob(os.path.join(session_path, "*.txt"))[0]
        metadata_file_path = glob(os.path.join(session_path, "*.json"))[0]
        student_name = os.path.normpath(session_path).split(os.sep)[-2]
    except IndexError:
        raise ValueError("Le répertoire {session_path} devrait contenir EXCLUSIVEMENT un fichier .txt contenant l'enregistrement " +
                         "de la session, et un fichier .json de métadonnées")
    
    
    # CHARGEMNENT DE LA SESSION
    
    with open(recording_file_path, 'r') as f:
        txt_file_raw_content = f.readlines()
        
    with open(metadata_file_path, 'r') as meta_file:
        metadata_json = json.load(meta_file)
        
    session = load_session(metadata_json, txt_file_raw_content)
    
    # ENREGISTREMENT EN FICHIERS JSON
    # print(f"Enregistrement des fichiers JSON dans le répertoire payload_data/{student_name}/")
    # save_session_input_to_json(session_input=session, student_name=student_name)
    
    # ENVOI AU SERVEUR
    
    post_session_input_to_server(session_input=session, url=url, auth_token=auth_token)