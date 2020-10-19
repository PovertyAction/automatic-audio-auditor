import os
from pydub import AudioSegment
import numpy as np
import azure_transcribe

def increase_sound_volume(sound, amount):
    return sound + amount

def get_audio_duration(audio_url):
  #Check that file exists
  if not os.path.exists(audio_url):
      return False

  #Read file
  sound = AudioSegment.from_file(audio_url)
  return sound.duration_seconds

def generate_transcript(audio_url, language='en', increase_volume=False):
  '''
  Given the url of a file and a specified language, outputs its transcript using azure speech recognition API
  '''

  #Check that file exists
  if not os.path.exists(audio_url):
      return False

  #Read file
  sound = AudioSegment.from_file(audio_url)

  #Transform to .wav
  AUDIO_FILE_WAV = "transcript.wav"
  sound.export(AUDIO_FILE_WAV, format="wav")

  if increase_volume:
    sound = increase_sound_volume(sound, 100)

  #Generate transcript
  transcription = azure_transcribe.generate_transcript(AUDIO_FILE_WAV)

  return transcription


if __name__ =='__main__':

    audio_url = "X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\Audio Audits (Consent)\AA_0199ef62-8639-43a7-b156-a6914f1396be-audio_audit_cons_c_call_phone.m4a"
    language = 'es-CO'

    print(f'Duration: {get_audio_duration(audio_url)}')

    print(f'Transcript {generate_transcript(audio_url, language)}')
