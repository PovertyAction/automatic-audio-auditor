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

import numpy as np
import os

from os import path
import sys
sys.path.append(path.abspath('../../All-Deepspeech/DeepSpeech-examples'))
sys.path.append(path.abspath('../../All-Deepspeech/DeepSpeech-examples/vad_transcriber'))
from vad_transcriber import wavTranscriber
from vad_transcriber import wavSplit
import wav_transformer

#Parameters
segment_generation_aggressive = 3
audio_path = '/mnt/x/Box Sync/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media/AA_029afeb8-cf16-468f-9d86-2f79ad8978ee_cons2_audio.m4a'

#Transform to wav
wav_transformer.transform_to_wav(audio_path, 'wav_copy.wav')

#Create segments of audio, to create small chunks
segments, sample_rate, audio_length = wavTranscriber.vad_segment_generator('wav_copy.wav', segment_generation_aggressive)

#For each segment, create and save wav file if their duration is >1 sec
for i, segment in enumerate(segments):

    print("Processing chunk %002d" % (i,))
    audio = np.frombuffer(segment, dtype=np.int16)

    output_file_name = str(i)+'_hola.wav'

    wavSplit.write_wave(output_file_name, audio, 16000)

    #If duration less than a second, delete it
    pcm_data, sample_rate, duration = wavSplit.read_wave(output_file_name)
    if duration<1:
        os.remove(output_file_name)
        print(f'{i} deleted')
