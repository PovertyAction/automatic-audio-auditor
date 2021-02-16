# Steps:
'''
1. Load .m4a surveyCTO media file
2. Transform to wav
3. Cut audio in small pieces (10-15 sec) and transform to 16khz, using vad_segment_generator

Pending:
# Capture transcript from Azure transcripts_cache.json
# Create train.csv with all audio pieces and their transcription
'''
###

import os
import sys
import string

import numpy as np
import pandas as pd


import wav_transformer

#Import modules from vad_transcriber examples, used to generate audio segments
sys.path.append(os.path.abspath('../../../All-Deepspeech/DeepSpeech-examples/vad_transcriber'))
import wavTranscriber
import wavSplit

#Import audio auditor modules
sys.path.append(os.path.abspath('../..'))
import db_manager
from file_names import *

#Import Azure module to generate transcriptions
# sys.path.append(os.path.abspath('../../Azure'))
from Azure import azure_transcribe

#Parameters
segment_generation_aggressive = 3

def get_audio_paths(media_folder):
    #PENDINGS
    audio_audits_paths_df = pd.read_csv('/mnt/c/Users/felip/ml_for_survey_data_quality/audio_audits_paths.csv')
    audio_paths_list = audio_audits_paths_df['audio_audit_survey'].tolist()

    #Clean anjd complete audios path
    full_audio_paths_list = [media_folder+'/'+path.split('\\')[1] for path in audio_paths_list]

    return full_audio_paths_list

def create_audio_chunks(audio_chunks_dir, audio_file_name, audio_path):

    #Transform to wav
    wav_copy_path = audio_chunks_dir+'/'+audio_file_name+'_wav_copy.wav'

    wav_transformer.transform_to_wav(audio_path, wav_copy_path)

    #Create segments of audio, to create small chunks
    segments, sample_rate, audio_length = wavTranscriber.vad_segment_generator(wav_copy_path, segment_generation_aggressive)

    #Remove wav copy
    os.remove(wav_copy_path)

    #For each segment, create and save wav file if their duration is >1 sec
    for i, segment in enumerate(segments):

        print("Processing chunk %002d" % (i,))
        audio = np.frombuffer(segment, dtype=np.int16)

        output_file_name = audio_chunks_dir+'/'+str(i)+'_chunck.wav'

        wavSplit.write_wave(output_file_name, audio, 16000)

        #If duration less than a second, delete it
        pcm_data, sample_rate, duration = wavSplit.read_wave(output_file_name)
        if duration<1:
            os.remove(output_file_name)
            print(f'{i} deleted')

    #Once finished, we create a file that signals that we have created all chunks
    file = open(audio_chunks_dir+"/all_chunks_created.txt", "w")
    file.write("All chunks have been created")
    file.close()

def get_all_chunks_path(directory):

    only_files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    only_wav = [f for f in only_files if f.split('.')[1]=="wav"]
    return sorted(only_wav)

def all_chunks_already_created(chunks_dir):
    #We know that all_chunks have been created if a file named 'all_chunks_created.txt' exist in the chunk dir
    return os.path.isfile(chunks_dir+"/all_chunks_created.txt")

def remove_punctuations(chunk_transcript):
    chunk_transcript = chunk_transcript.translate(str.maketrans('', '', string.punctuation))
    for c in [',','.','¿','?','¡','!','"','º']:
        chunk_transcript = chunk_transcript.replace(c,'')
    return chunk_transcript

def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def create_training_set(project_name, media_folder, testing=False):

    all_audios_paths = get_audio_paths(media_folder)

    #Create folder for outputs
    outputs_directory = '/mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/'+project_name
    if not os.path.exists(outputs_directory):
        os.mkdir(outputs_directory)

    #Load transcripts cache



    transcripts_cache = db_manager.load_database(DS_TRAINING_TRANSCRIPTS_DB_FILE_NAME)

    df_rows = []
    for audio_index, audio_path in enumerate(all_audios_paths):

        print(f'Working on audio {audio_path.split("media")[1]}')
        if testing and audio_index>30:
            break

        #Create directory for this audio outputs
        audio_file_name = audio_path.split('/')[-1].split('.')[0]
        chunks_dir = outputs_directory+'/'+audio_file_name
        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)

        #Create audio chunks if they havent been created yet
        if not all_chunks_already_created(chunks_dir):
            print('Creating chunks')
            create_audio_chunks(chunks_dir, audio_file_name, audio_path)
        else:
            print('All chunks already created')

        #For each audio chunk, get its size, transcript, and append it to training_set_df
        for chunk_index, chunk_path in enumerate(get_all_chunks_path(chunks_dir)):
            # if testing:
            #     if chunk_index==0:
            #         continue
            #     if chunk_index>2:
            #         break

            chunk_size = os.path.getsize(chunk_path)

            #First lets check if transcript is already existing in db
            chunk_transcript = db_manager.get_element_from_database(
                database = transcripts_cache,
                project_name = project_name,
                case_id = audio_file_name,
                q_code = str(chunk_index))

            # if chunk_transcript:
            #     print(f'Found transcript for {project_name} {audio_file_name} {chunk_index}')
            #If we didnt find transcript in db, generate it and save it
            if chunk_transcript is None:
                print(f'Generating transcript for {project_name} {audio_file_name} {chunk_index}')
                chunk_transcript = azure_transcribe.generate_transcript(chunk_path, language='es-CO', return_list=False)
                print(chunk_transcript)

                db_manager.save_to_db(
                    database = transcripts_cache,
                    database_file_name = DS_TRAINING_TRANSCRIPTS_DB_FILE_NAME,
                    project_name = project_name,
                    case_id = audio_file_name,
                    q_code = str(chunk_index),
                    element_to_save = chunk_transcript)

            #We do not want to train our model with empty transcripts
            if chunk_transcript != '':

                #Transform trancript to lower case and remove punctuations, deepspeech works better that way
                chunk_transcript = chunk_transcript.lower()
                chunk_transcript = remove_punctuations(chunk_transcript)

                #We are currently not being able to capture numbers as words (instead of digits) when generating transcripts. Until then, we wont consider transcripts that are only numbers
                if not represents_int(chunk_transcript):
                    df_rows.append([chunk_path, chunk_size, chunk_transcript])
            #     else:
            #         print(f'Not considering {chunk_transcript} cause its pure number')
            # else:
            #     print(f'Not considering {chunk_transcript} cause its empty')

        print('Transcrips for chunks ready\n')

    #Create .csv for training, dev and test
    #We will use 60% of data for training, 20% for dev and 20% for testing

    amount_rows = len(df_rows)
    train_rows = df_rows[0:int(amount_rows*0.6)]
    dev_rows = df_rows[int(amount_rows*0.6):int(amount_rows*0.8)]
    test_rows = df_rows[int(amount_rows*0.8):]

    for (file_name, rows_data) in \
        [('train', train_rows),
       ('dev', dev_rows),
       ('test', test_rows)]:

       #Create df
       set_df = pd.DataFrame()

       #Add rows to df
       set_df = set_df.append(rows_data)

       #Set columns names
       set_df.columns=['wav_filename', 'wav_filesize', 'transcript']

       #Create csv
       set_df.to_csv(outputs_directory+'/'+file_name+'.csv', index=False)



if __name__ == '__main__':
    project_name = 'RECOVER-RD3-COL'
    media_folder = '/mnt/x/Box Sync/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media'
    create_training_set(project_name, media_folder, testing=True)
