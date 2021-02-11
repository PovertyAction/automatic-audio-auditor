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

#Temporal, should be replaced by merge in master
def save_in_cache(project_name, case_id, q_code, transcription_no_abb):
    if project_name not in transcripts_cache:
        transcripts_cache[project_name] = {}
    if case_id not in transcripts_cache[project_name]:
        transcripts_cache[project_name][case_id] = {}

    transcripts_cache[project_name][case_id][q_code] = transcription_no_abb
    #Save to file
    with open('transcripts_cache.json', 'w') as transcripts_cache_json_file:
        json.dump(transcripts_cache, transcripts_cache_json_file)
        transcripts_cache_json_file.close()

def generate_transcript(project_name, case_id, q_code, audio_url, language, first_q_offset, ta_row=None, previous_ta_row=None, next_ta_row=None, increase_volume=False, look_for_transcript_in_cache=True, duration=None, offset=None, save_transcript_in_cache=True, show_debugging_prints=True, show_azure_debugging_prints=False):
    '''
    Given the url of a file and a specified language, outputs its transcript using azure speech recognition API.
    '''
    global show_prints
    show_prints = show_debugging_prints

    global previous_transcription

    #Check that file exists
    if not os.path.exists(audio_url):
        print_if_debugging(f'{audio_url} does not exist')
        return False

    #Check if questions exist in transcript cache
    if  look_for_transcript_in_cache and \
        project_name in transcripts_cache.keys() and \
        case_id in transcripts_cache[project_name] and \
        q_code in transcripts_cache[project_name][case_id]:
            print(f'Using cached transcript for {project_name} {case_id} {q_code}')
            return transcripts_cache[project_name][case_id][q_code]
    else:
        if check_cache_has_transcript(project_name, case_id, q_code):
            print('wwwwwwwwwwwwaaaaaaaaaaat')

    #If question has same timeframe as previous question, return previous transcript
    if same_timeframe_as_previous_question(ta_row, previous_ta_row) and previous_transcription:
        print(f'Using previous transcription for {project_name} {case_id} {q_code}')
        if save_transcript_in_cache:
            save_in_cache(project_name, case_id, q_code, previous_transcription)
        return previous_transcription

    print_if_debugging(f'Generating transcript for {project_name} {case_id} {q_code}')

    #Read file
    sound = AudioSegment.from_file(audio_url)

    #If offset and duration where not given as arguments, eigher find them in text audit or set it to 0 and total length
    if offset is None and duration is None:
        if ta_row is not None:
            offset, duration = get_first_appeared_and_duration(ta_row=ta_row, previous_ta_row=previous_ta_row, next_ta_row=next_ta_row, first_q_offset=first_q_offset)
        else:
            offset = 0
            duration = sound.duration_seconds

    #Chop sound according to offset and duration given
    if offset is not None and duration is not None: #I think that at this point this if condition can never be false
      sound = sound[offset*1000:(offset+duration)*1000]##pydub works in milliseconds

    #Transform to .wav
    AUDIO_FILE_WAV = "transcript.wav"
    sound.export(AUDIO_FILE_WAV, format="wav")

    if increase_volume:
        sound = increase_sound_volume(sound, 100)

    #Generate transcript
    transcription = azure_transcribe.generate_transcript(AUDIO_FILE_WAV, language, show_azure_debugging_prints)

    #Replace abbreviations for full words
    transcription_no_abb = [replace_abbreviations(phrase) for phrase in transcription]

    previous_transcription = transcription_no_abb

    #Save transcript in transcript_cache
    if save_transcript_in_cache:
        save_in_cache(project_name, case_id, q_code, transcription_no_abb)

    print_if_debugging(f'Transcript {transcription_no_abb}')
    return transcription_no_abb


def check_cache_has_transcript(project_name, case_id, question_code):
    if project_name in transcripts_cache and \
        case_id in transcripts_cache[project_name] and \
        question_code in transcripts_cache[project_name][case_id]:
        return True
    else:
        return False


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


if __name__ =='__main__':

    audio_url = "X:\\Box Sync\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\media\\AA_9ded1778-0639-4e1b-8051-e4ce3bb3a94e_cons2_audio.m4a"
    language = 'es-CO'

    # 13:24-13:58
    duration=None
    offset=None

    print(generate_transcript(project_name='example_project_name', case_id='example_case_id', q_code='example_q_code', audio_url=audio_url, language=language, first_q_offset=0, look_for_transcript_in_cache=False, duration=duration, offset=offset, save_transcript_in_cache=False, show_debugging_prints=True, show_azure_debugging_prints=True))



    # for project_name, case_id, question_code in [('RECOVER_RD3_COL', '11925', 'chd8_5'), ('RECOVER_RD3_COL', '13364', 'chd8_3')]:
    #     print((project_name, case_id, question_code))
    #     print(check_cache_has_transcript(project_name, case_id, question_code))


    # #Printing transcripts of a particular question
    # project_name = 'RECOVER_RD3_COL'
    # question = 'cov1c'
    # def print_transcripts_of_question(project_name, question_code):
    #     for case_id in transcripts_cache[project_name].keys():
    #         if question_code in transcripts_cache[project_name][case_id]:
    #             print(transcripts_cache[project_name][case_id][question_code])
    # print_transcripts_of_question(project_name, question)



    # print(f'Duration: {get_audio_duration(audio_url)}')
    #
    # print(f'Transcript {generate_transcript(audio_url, language)}')
