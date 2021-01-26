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

import numpy as np
import pandas as pd


import wav_transformer

#Import modules from vad_transcriber examples, used to generate audio segments
sys.path.append(os.path.abspath('../../../All-Deepspeech/DeepSpeech-examples/vad_transcriber'))
import wavTranscriber
import wavSplit

#Import audio auditor modules
sys.path.append(os.path.abspath('../..'))
import transcript_generator
import transcripts_cache_manager

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


def create_training_set(project_name, transcripts_cache_file, media_folder, testing=False):

    all_audios_paths = get_audio_paths(media_folder)

    #Create folder for outputs
    outputs_directory = '/mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/'+project_name
    if not os.path.exists(outputs_directory):
        os.mkdir(outputs_directory)

    #Load transcripts cache
    transcripts_cache = transcripts_cache_manager.load_cache(transcripts_cache_file)

    df_rows = []
    for audio_index, audio_path in enumerate(all_audios_paths):

        if testing and audio_index>5:
            break


        #Create directory for this audio outputs
        audio_file_name = audio_path.split('/')[-1].split('.')[0]
        chunks_dir = outputs_directory+'/'+audio_file_name
        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)

        #Create audio chunks if they havent been created yet
        if not all_chunks_already_created(chunks_dir):
            print('All chunks not created, creating them now')
            create_audio_chunks(chunks_dir, audio_file_name, audio_path)
        else:
            print('All chunks already created')

        #For each audio chunk, get its size, transcript, and append it to training_set_df
        for chunk_index, chunk_path in enumerate(get_all_chunks_path(chunks_dir)):
            if testing:
                if chunk_index==0:
                    continue
                if chunk_index>2:
                    break

            chunk_size = os.path.getsize(chunk_path)

            chunk_transcript, new_transcript = transcript_generator.generate_transcript(project_name=project_name, case_id=audio_file_name, q_code=str(chunk_index), audio_url=chunk_path, language='es-CO', first_q_offset=0, look_for_transcript_in_cache=True, transcripts_cache=transcripts_cache, show_debugging_prints=True, show_azure_debugging_prints=False, return_list_phrases=False)

            if chunk_transcript != '':
                print([chunk_path, chunk_size, chunk_transcript])
                df_rows.append([chunk_path, chunk_size, chunk_transcript.replace('"', '')])

                if new_transcript:
                    transcripts_cache_manager.add_transcript_to_cache(transcripts_cache=transcripts_cache, project_name=project_name, case_id=audio_file_name, q_code=str(chunk_index), transcript=chunk_transcript)
                    transcripts_cache_manager.save_cache(transcripts_cache, transcripts_cache_file)
    #Create .csv
    training_set_df = pd.DataFrame()
    training_set_df = training_set_df.append(df_rows)
    training_set_df.columns=['wav_filename', 'wav_filesize', 'transcript']
    training_set_df.to_csv(outputs_directory+'/train.csv', index=False)



if __name__ == '__main__':
    project_name = 'RECOVER-RD3-COL'
    media_folder = '/mnt/x/Box Sync/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media'
    transcripts_cache_file = 'deepspeech_training_cache.json'
    create_training_set(project_name, transcripts_cache_file, media_folder, testing=False)
