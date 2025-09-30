import argparse
import os
from src.utils import raw_to_df
import json

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outil pour transformer des fichiers en données traitées.")
    parser.add_argument("fichier", help="Chemin du fichier à analyser")
    
    # Parsing du chemin d'accès, pour l'exécution il suffit de faire "python main.py <chemin_vers_le_fichier.txt>"
    args = parser.parse_args()
    file_path = args.fichier
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Le chemin {file_path} que vous avez renseigné n'existe pas.")
    if not file_path.endswith(".txt"):
        raise ValueError(f"Le fichier {file_path} que vous avez renseigné n'est pas un fichier .txt")
    
    with open(file_path, 'r') as file:
        file_content = file.readlines()
    
    header_json = raw_to_df(file_content)
    
    print(json.dumps(header_json, indent=4, ensure_ascii=False))
    
