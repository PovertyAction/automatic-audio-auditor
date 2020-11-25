import os
from pydub import AudioSegment
import numpy as np
import azure_transcribe
import json

abbreviations = {
    'Ppal.': 'principal',
    'Dpto.': 'departamento',
    'N.': 'numero',
    'N.º': 'numero'}

transcripts_cache = None
previous_transcription = None

debugging = False
def print_if_debugging(text):
    if debugging:
        print(text)

def increase_sound_volume(sound, amount):
    return sound + amount

def get_audio_duration(audio_url):
    #Check that file exists
    if not os.path.exists(audio_url):
      return False

    #Read file
    sound = AudioSegment.from_file(audio_url)
    return sound.duration_seconds

def replace_abbreviations(phrase):
    phrase_no_abb = []

    for word in phrase.split(" "):
        if word in abbreviations:
            word = abbreviations[word]
        phrase_no_abb.append(word)

    return " ".join(phrase_no_abb)

def same_timeframe_as_previous_question(ta_row, previous_ta_row):
    if previous_ta_row is None:
        return False

    if  get_first_appeared_and_duration(ta_row=ta_row) == \
        get_first_appeared_and_duration(ta_row=previous_ta_row):
        return True
    else:
        return False

def get_first_appeared_and_duration(ta_row, first_q_offset=0, previous_ta_row=None, next_ta_row=None):
    q_first_appeared = ta_row['First appeared (seconds into survey)']-first_q_offset

    #Sometimes duration is longer than it should (given back and forths), so we will choose duration = difference between next q starting point and current one, if duration reported is too long.
    q_duration = ta_row['Total duration (seconds)']

    if next_ta_row is not None:
        next_q_first_appeared = next_ta_row['First appeared (seconds into survey)']-first_q_offset

        if next_q_first_appeared-q_first_appeared<q_duration and next_q_first_appeared!=q_first_appeared: #Be sure they dont have the same starting point (grouped questions)
            print_if_debugging('fixing q duration!!!!!!!!!!!!!!!')
            print_if_debugging(f'next_q_first_appeared {next_q_first_appeared}')
            print_if_debugging(f'q_first_appeared {q_first_appeared}')
            print_if_debugging(f'q_duration {q_duration}')

            q_duration = next_q_first_appeared-q_first_appeared

    return q_first_appeared, q_duration+1

def previous_transcript_to_none():
    global previous_transcription
    previous_transcription = None

def generate_transcript(project_name, case_id, q_code, audio_url, language, first_q_offset, ta_row=None, previous_ta_row=None, next_ta_row=None, increase_volume=False):
    '''
    Given the url of a file and a specified language, outputs its transcript using azure speech recognition API.
    '''
    global previous_transcription

    #Check that file exists
    if not os.path.exists(audio_url):
        print_if_debugging(f'{audio_url} does not exist')
        return False

    #Check if questions exist in transcript cache
    if  project_name in transcripts_cache.keys() and \
        case_id in transcripts_cache[project_name] and \
        q_code in transcripts_cache[project_name][case_id]:
            print('Using cached transcript')
            return transcripts_cache[project_name][case_id][q_code]

    #If question has same timeframe as previous question, return previous transcript
    if same_timeframe_as_previous_question(ta_row, previous_ta_row):

        if previous_transcription: #Maybe we have the same timeframe
            print('Using previous transcription')
            return previous_transcription

    print(f'Generating transcript for {project_name} {case_id} {q_code}')

    #Get offset and duration fo question in audio record
    offset, duration = get_first_appeared_and_duration(ta_row=ta_row, previous_ta_row=previous_ta_row, next_ta_row=next_ta_row, first_q_offset=first_q_offset)

    #Read file
    sound = AudioSegment.from_file(audio_url)

    #Chop if offset and duration give
    if offset is not None and duration is not None:
      sound = sound[offset*1000:(offset+duration)*1000]##pydub works in milliseconds

    #Transform to .wav
    AUDIO_FILE_WAV = "transcript.wav"
    sound.export(AUDIO_FILE_WAV, format="wav")

    if increase_volume:
        sound = increase_sound_volume(sound, 100)

    #Generate transcript
    transcription = azure_transcribe.generate_transcript(AUDIO_FILE_WAV)

    #Replace abbreviations for full words
    transcription_no_abb = [replace_abbreviations(phrase) for phrase in transcription]

    previous_transcription = transcription_no_abb

    #Save transcript in transcript_cache
    if project_name not in transcripts_cache:
        transcripts_cache[project_name] = {}
    if case_id not in transcripts_cache[project_name]:
        transcripts_cache[project_name][case_id] = {}

    transcripts_cache[project_name][case_id][q_code] = transcription_no_abb
    #Save to file
    with open('transcripts_cache.json', 'w') as transcripts_cache_json_file:
        json.dump(transcripts_cache, transcripts_cache_json_file)

    return transcription_no_abb

def load_transcripts_cache():
    global transcripts_cache

    #If transcripts cache json file does not exist, create it
    if not os.path.exists('transcripts_cache.json'):
        with open("transcripts_cache.json", "w") as outfile:
            json.dump({}, outfile)

    with open("transcripts_cache.json") as transcripts_cache_json_file:
        transcripts_cache = json.load(transcripts_cache_json_file)

load_transcripts_cache()

if __name__ =='__main__':

    audio_url = "X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\Audio Audits (Consent)\AA_0199ef62-8639-43a7-b156-a6914f1396be-audio_audit_cons_c_call_phone.m4a"
    language = 'es-CO'

    generate_transcript('example_project_name', 'example_case_id', 'example_q_code', audio_url, 'example_language', 0)

    # print(f'Duration: {get_audio_duration(audio_url)}')
    #
    # print(f'Transcript {generate_transcript(audio_url, language)}')
