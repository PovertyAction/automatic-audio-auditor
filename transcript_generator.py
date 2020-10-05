import speech_recognition as sr
import os
from pydub import AudioSegment

def increase_sound_volume(sound, amount):
    return sound + amount

def generate_transcript(audio_url, language='en', adjust_for_ambient_noise=False, increase_volume=False, offset=None, duration=None):
  '''
  Given the url of a file and a specified language, outputs its transcript using google API
  Reference https://realpython.com/python-speech-recognition/
  '''
  #Read file
  sound = AudioSegment.from_file(audio_url)

  #Transform to .wav
  AUDIO_FILE_WAV = "transcript.wav"
  sound.export(AUDIO_FILE_WAV, format="wav")

  if increase_volume:
    sound = increase_sound_volume(sound, 100)

  #Generate transcript
  r = sr.Recognizer()

  #Transform raw audio to AudioFileType
  with sr.AudioFile(AUDIO_FILE_WAV) as source:
    if (adjust_for_ambient_noise):
        r.adjust_for_ambient_noise(source)

    #Transform source to AudioData type, which can be read by the transcript API
    audio = r.record(source, offset=offset, duration=duration)

    #Use API to generate transcript
    transcript = r.recognize_google(audio, language=language)

    return transcript

if __name__ =='__main__':

    audio_url = "X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\Audio Audits (Consent)\AA_01411b0c-5395-4065-8118-8c21edcbafac-audio_audit_cons_c_call_phone.m4a"
    language = 'es-CO'

    print(f'Transcript {generate_transcript(audio_url, language)}')
    print(f'Transcript {generate_transcript(audio_url, language, adjust_for_ambient_noise=True)}')
    print(f'Transcript {generate_transcript(audio_url, language, adjust_for_ambient_noise=True, increase_volume=True)}')
