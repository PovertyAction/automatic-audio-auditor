import os
from pydub import AudioSegment
import numpy as np
import json
import db_manager
from file_names import *

from Azure import azure_file_management
from Azure import azure_transcribe
from Azure import azure_batch_transcribe

abbreviations = {
    'Ppal.': 'principal',
    'Dpto.': 'departamento',
    'N.': 'numero',
    'N.º': 'numero',
    'N.º.': 'numero'}

transcripts_cache = None
previous_transcription = None
show_prints = False
def print_if_debugging(text):
    if show_prints:
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
            q_duration = next_q_first_appeared-q_first_appeared

    return q_first_appeared, q_duration+1

def previous_transcript_to_none():
    global previous_transcription
    previous_transcription = None

def run_live_transcriptions(language):

    #Load transcripts tasks
    global transcript_tasks_db
    transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)

    #Load transcripts cache
    global transcript_cache
    transcript_cache = db_manager.load_database(TRANSCRIPTS_CACHE_FILE_NAME)

    #Find tasks in pending status
    for project in transcript_tasks_db.keys():
      for case_id in transcript_tasks_db[project].keys():
          for q_code in transcript_tasks_db[project][case_id].keys():

              if transcript_tasks_db[project][case_id][q_code]['status']=='PENDING':

                  task = transcript_tasks_db[project][case_id][q_code]

                  #Create audio file for this task
                  choped_wav_file_path = create_choped_wav(
                      audio_url = task['audio_url'],
                      offset = task['offset'],
                      duration = task['duration'])


                  #Generate transcript
                  transcription = azure_transcribe.generate_transcript(choped_wav_file_path, language)
                  print(f'Transcript for {project} {case_id} {q_code} ready')

                  #Replace abbreviations for full words
                  transcription_no_abb = [replace_abbreviations(phrase) for phrase in transcription]
                  print(transcription_no_abb)
                  #Remove audio chop
                  os.remove(choped_wav_file_path)

                  #Save transcript
                  transcript_cache[project][case_id][q_code] = transcription_no_abb
                  db_manager.save_db(transcript_cache, TRANSCRIPTS_CACHE_FILE_NAME)

                  #Change task status
                  transcript_tasks_db[project][case_id][q_code]['status'] = 'SUCCEDED'
                  db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)


def create_choped_wav(audio_url, offset, duration):

    #Read file
    sound = AudioSegment.from_file(audio_url)

    #Chop sound according to offset and duration given
    if offset is not None and duration is not None:
      sound = sound[offset*1000:(offset+duration)*1000]##pydub works in milliseconds

    #Transform to .wav
    AUDIO_FILE_WAV = "transcript.wav"
    out = sound.export(AUDIO_FILE_WAV, format="wav")
    out.close()
    return AUDIO_FILE_WAV


def launch_transcript_tasks(trancript_engine, language):

    #Load transcripts tasks
    global transcript_tasks_db
    transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)

    if trancript_engine == 'azure_batch':
        #Find tasks in data_uplodaded status
        for project in transcript_tasks_db.keys():
            for case_id in transcript_tasks_db[project].keys():
                for q_code in transcript_tasks_db[project][case_id].keys():

                    if transcript_tasks_db[project][case_id][q_code]['status']=='DATA_UPLOADED':

                        transcription_id = azure_batch_transcribe.launch_transcription(locale=language, blob_name = transcript_tasks_db[project][case_id][q_code]['blob_name'])

                        transcript_tasks_db[project][case_id][q_code]['status'] = 'TRANSCRIPTION_IN_PROGRESS'

                        transcript_tasks_db[project][case_id][q_code]['transcription_id'] = transcription_id

                        db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)

def get_transcription_results(trancript_engine):

    #Load transcripts tasks
    global transcript_tasks_db
    transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)

    #Load transcripts cache
    global transcript_cache
    transcript_cache = db_manager.load_database(TRANSCRIPTS_CACHE_FILE_NAME)

    if trancript_engine == 'azure_batch':

        #Find tasks in TRANSCRIPTION_IN_PROGRESS status
        for project in transcript_tasks_db.keys():
            for case_id in transcript_tasks_db[project].keys():
                for q_code in transcript_tasks_db[project][case_id].keys():

                    if transcript_tasks_db[project][case_id][q_code]['status']=='TRANSCRIPTION_IN_PROGRESS':

                        transcription_id = transcript_tasks_db[project][case_id][q_code]['transcription_id']

                        result = azure_batch_transcribe.get_transcription_result(transcription_id=transcription_id)

                        if result:
                            transcript_tasks_db[project][case_id][q_code]['status'] = 'SUCCEDED'
                            transcript_cache[project][case_id][q_code] = result

                            db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)
                            db_manager.save_db(transcript_cache, TRANSCRIPTS_CACHE_FILE_NAME)
                        else:
                            transcript_tasks_db[project][case_id][q_code]['status'] = 'FAILED'
                            db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)



def upload_transcript_tasks_audio_files(trancript_engine):

    #Load transcripts tasks
    global transcript_tasks_db
    transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)

    if trancript_engine == 'azure_batch':

        #Find tasks in pending status
        for project in transcript_tasks_db.keys():
            for case_id in transcript_tasks_db[project].keys():
                for q_code in transcript_tasks_db[project][case_id].keys():

                    if transcript_tasks_db[project][case_id][q_code]['status']=='PENDING':

                        task = transcript_tasks_db[project][case_id][q_code]

                        #Create audio file for this task
                        choped_wav_file_path = create_choped_wav(
                            audio_url = task['audio_url'],
                            offset = task['offset'],
                            duration = task['duration'])

                        #Upload files to container
                        blob_name = f'{project}_{case_id}_{q_code}'

                        upload_status = azure_file_management.upload_blob(
                            file_path = choped_wav_file_path,
                            blob_name = blob_name)

                        #Remove audio chop
                        os.remove(choped_wav_file_path)

                        #Change task status
                        transcript_tasks_db[project][case_id][q_code]['status'] = 'DATA_UPLOADED'
                        transcript_tasks_db[project][case_id][q_code]['blob_name'] = blob_name

                        db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)

                        if not upload_status:
                            print(f'Error when uploading {project} {case_id} {q_code}')
