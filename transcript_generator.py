import os
from pydub import AudioSegment
import numpy as np
import json
import time
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

def tasks_are_equal(task1, task2):

    #Check if any of the keys is different
    for key in ['audio_url', 'offset', 'duration']:
        if task1[key] != task2[key]:
            return False
    return True

def get_equivalent_succeded_question(transcript_tasks_db, project, case_id, q_code, task):
    '''
    Check if transcript_tasks_db has a task for a question with same timeframe as q_code
    '''
    ##Check we are not speaking about the same question, that questions have same timeframe and that other question is succeded
    for other_question in transcript_tasks_db[project][case_id]:
        if other_question != q_code and \
            tasks_are_equal(task, transcript_tasks_db[project][case_id][other_question]) and \
            transcript_tasks_db[project][case_id][other_question]['status'] == 'SUCCEDED':

            return other_question
    return None


def run_live_transcriptions(language):

    #Load transcripts tasks
    global transcript_tasks_db
    transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)

    #Load transcripts cache
    global transcript_cache
    transcript_cache = db_manager.load_database(TRANSCRIPTS_CACHE_FILE_NAME)

    #Find tasks in pending status
    total_n_pending_tasks=0
    for project in transcript_tasks_db.keys():
      for case_id in transcript_tasks_db[project].keys():
          for q_code in transcript_tasks_db[project][case_id].keys():

              if transcript_tasks_db[project][case_id][q_code]['status']=='PENDING':
                  total_n_pending_tasks+=1

    #Find tasks in pending
    task_i=1
    for project in transcript_tasks_db.keys():
      for case_id in transcript_tasks_db[project].keys():
          for q_code in transcript_tasks_db[project][case_id].keys():

              if transcript_tasks_db[project][case_id][q_code]['status']=='PENDING':
                  print(f'Working task {task_i}/{total_n_pending_tasks}')

                  start_time = time.time()
                  task = transcript_tasks_db[project][case_id][q_code]


                  transcript = None

                  #We know that some tasks are repetitive, in the sense that some questions have the same timeframe than others. This happens for grouped questions
                  #If that is the case, rather than generating the transcript twice, we will copy the transcript from the equivalent question
                  equivalent_succeded_q = get_equivalent_succeded_question(transcript_tasks_db, project, case_id, q_code, task)
                  if equivalent_succeded_q:
                      equivalent_transcript = db_manager.get_element_from_database(transcript_cache, project, case_id, equivalent_succeded_q)
                      if equivalent_transcript:
                          transcript = equivalent_transcript
                          print(f'For {project} {case_id} {q_code}, we will use same transcript as {equivalent_succeded_q}')
                          # print(transcript)
                      else:
                          raise ValueError(f"Succeding task does not have transcript {project} {case_id} {equivalent_succeded_q}")

                  #If we did not get transcript from an equivalent question, calculate it
                  if transcript is None:
                      #Create audio file for this task
                      choped_wav_file_path = create_choped_wav(
                          audio_url = task['audio_url'],
                          offset = task['offset'],
                          duration = task['duration'])

                      #Generate transcript
                      transcript = azure_transcribe.generate_transcript(choped_wav_file_path, language, show_debugging_prints=False)
                      print(f'Transcript for {project} {case_id} {q_code} ready')
                      print(transcript)
                      #Remove audio chop
                      os.remove(choped_wav_file_path)

                  #Save transcript
                  db_manager.save_to_db(
                      database=transcript_cache,
                      database_file_name=TRANSCRIPTS_CACHE_FILE_NAME,
                      project_name=project,
                      case_id=case_id,
                      q_code=q_code,
                      element_to_save=transcript)

                  #Change task status
                  transcript_tasks_db[project][case_id][q_code]['status'] = 'SUCCEDED'
                  db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)

                  task_i+=1
                  end_time = time.time()
                  print(f'Task took {end_time-start_time} seconds')
                  print(f"Audio file duration {task['duration']}")
                  print(f"{task['duration']/(end_time-start_time)} audio data processes per sec")

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

                        transcription_id = azure_batch_transcribe.launch_transcription(locale=language, container_name = 'mycontainer', blob_name = transcript_tasks_db[project][case_id][q_code]['blob_name'])

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

                            #Now we can delete the blob in azure
                            azure_file_management.delete_blob(container_name = 'mycontainer', blob_name=transcript_tasks_db[project][case_id][q_code]['blob_name'])
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
                            container_name = 'mycontainer',
                            blob_name = blob_name)

                        #Remove audio chop
                        os.remove(choped_wav_file_path)

                        #Change task status
                        transcript_tasks_db[project][case_id][q_code]['status'] = 'DATA_UPLOADED'
                        transcript_tasks_db[project][case_id][q_code]['blob_name'] = blob_name

                        db_manager.save_db(transcript_tasks_db, TRANSCRIPT_TASKS_DB_FILE_NAME)

                        if not upload_status:
                            print(f'Error when uploading {project} {case_id} {q_code}')
