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

#Parameters
segment_generation_aggressive = 3

def get_audio_paths(media_folder):
    #PENDINGS
    audio_audits_paths_df = pd.read_csv('/mnt/c/Users/felip/ml_for_survey_data_quality/audio_audits_paths.csv')
    audio_paths_list = audio_audits_paths_df['audio_audit_survey'].tolist()

    #Clean anjd complete audios path
    full_audio_paths_list = [media_folder+'/'+path.split('\\')[1] for path in audio_paths_list]

    return full_audio_paths_list

def create_audio_chunks(project_name, audio_path):
    #Create directory for outputs
    file_name = audio_path.split('/')[-1].split('.')[0]
    outputs_directory = '/mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/'+project_name+'/'+file_name
    if os.path.exists(outputs_directory):
        return outputs_directory

    os.makedirs(outputs_directory)

    #Transform to wav
    wav_copy_path = outputs_directory+'/'+file_name+'_wav_copy.wav'
    wav_transformer.transform_to_wav(audio_path, wav_copy_path)

    #Create segments of audio, to create small chunks
    print(wav_copy_path)
    segments, sample_rate, audio_length = wavTranscriber.vad_segment_generator(wav_copy_path, segment_generation_aggressive)

    #Remove wav copy
    os.remove(wav_copy_path)

    #For each segment, create and save wav file if their duration is >1 sec
    for i, segment in enumerate(segments):

        print("Processing chunk %002d" % (i,))
        audio = np.frombuffer(segment, dtype=np.int16)

        output_file_name = outputs_directory+'/'+str(i)+'_chunck.wav'

        wavSplit.write_wave(output_file_name, audio, 16000)

        #If duration less than a second, delete it
        pcm_data, sample_rate, duration = wavSplit.read_wave(output_file_name)
        if duration<1:
            os.remove(output_file_name)
            print(f'{i} deleted')

    print(outputs_directory)
    return outputs_directory

def get_all_files_path(directory):

    only_files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return only_files

def create_training_set(project_name, media_folder, testing=False):

    all_audios_paths = get_audio_paths(media_folder)

    outputs_directory = '/mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/'+project_name
    if not os.path.exists(outputs_directory):
        os.mkdir(outputs_directory)

    df_rows = []
    for audio_path in all_audios_paths:

        chunks_dir = create_audio_chunks(project_name, audio_path)

        #For each audio chunk, get its size, transcript, and append it to training_set_df
        for chunk_index, chunk_path in enumerate(get_all_files_path(chunks_dir)):

            if testing:
                if chunk_index==0:
                    continue
                if chunk_index>2:
                    break

            chunk_size = os.path.getsize(chunk_path)

            chunk_transcript = transcript_generator.generate_transcript(project_name='example_project_name', case_id='example_case_id', q_code='example_q_code', audio_url=chunk_path, language='es-CO', first_q_offset=0, look_for_transcript_in_cache=False, save_transcript_in_cache=False,
            show_debugging_prints=False, show_azure_debugging_prints=False, return_list_phrases=False)

            if chunk_transcript != '':
                print([chunk_path, chunk_size, chunk_transcript])
                df_rows.append([chunk_path, chunk_size, chunk_transcript.replace('"', '')])

    #Create .csv
    training_set_df = pd.DataFrame()
    training_set_df = training_set_df.append(df_rows)
    training_set_df.columns=['wav_filename', 'wav_filesize', 'transcript']
    training_set_df.to_csv(outputs_directory+'/train.csv', index=False)



if __name__ == '__main__':
    project_name = 'RECOVER-RD3-COL'
    media_folder = '/mnt/x/Box Sync/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media'
    create_training_set(project_name, media_folder, testing=True)
