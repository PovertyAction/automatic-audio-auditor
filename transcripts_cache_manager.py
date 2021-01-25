import os
import json

def load_cache(transcripts_cache_file_path):

    #If transcripts cache json file does not exist, create it
    if not os.path.exists(transcripts_cache_file_path):
        with open(transcripts_cache_file_path, "w") as outfile:
            json.dump({}, outfile)

    with open(transcripts_cache_file_path) as transcripts_cache_json_file:
        transcripts_cache = json.load(transcripts_cache_json_file)
    return transcripts_cache

def add_transcript_to_cache(transcripts_cache, project_name, case_id, q_code, transcript):

    if project_name not in transcripts_cache:
        transcripts_cache[project_name] = {}
    if case_id not in transcripts_cache[project_name]:
        transcripts_cache[project_name][case_id] = {}

    transcripts_cache[project_name][case_id][q_code] = transcript

    return transcripts_cache

def save_cache(transcripts_cache, transcripts_cache_file):

    with open(transcripts_cache_file, 'w') as transcripts_cache_json_file:
        json.dump(transcripts_cache, transcripts_cache_json_file)
