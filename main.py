import argparse
import os
from src.utils import parse_raw, simple_line_plot, segment_plot, session_to_json
import json
from glob import glob

if __name__ == "__main__":
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
    except IndexError:
        raise ValueError("Le répertoire {session_path} devrait contenir EXCLUSIVEMENT un fichier .txt contenant l'enregistrement " +
                         "de la session, et un fichier .json de métadonnées")
    
    with open(recording_file_path, 'r') as f:
        file_content = f.readlines()
    
    header_json, df = parse_raw(file_content)

    with open(metadata_file_path, 'r') as meta_file:
        metadata = json.load(meta_file)
    
    # CONVERSION EN JSON POUR L'ENVOI SUR LE SERVEUR
    
    json_payload = session_to_json(df, header_json, metadata)
    
    path = os.path.normpath(session_path)
    student_name = path.split(os.sep)[-2]
    
    for payload in json_payload:
        output_path = os.path.join("payload_data", student_name, f"{payload["sessionId"]}-{payload["sequenceId"]}.json")
        with open(output_path, "w") as f:
            json.dump(payload, f, ensure_ascii=False, indent=4)
