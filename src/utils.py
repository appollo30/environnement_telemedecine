import pandas as pd
import numpy as np
import json

def raw_to_df(file_content):
    header = file_content[1][2:]
    header_json = json.loads(header)
    
    return header_json

