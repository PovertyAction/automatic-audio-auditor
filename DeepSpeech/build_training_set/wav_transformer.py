from pydub import AudioSegment

def transform_to_wav(audio_url, output_file_name, offset=None, duration=None):

    #Read file
    sound = AudioSegment.from_file(audio_url)

    # #Chop if offset and duration give
    if offset is not None and duration is not None:
      sound = sound[offset*1000:(offset+duration)*1000]##pydub works in milliseconds

    #Transform to .wav
    out = sound.export(output_file_name, format="wav")
    out.close()

if __name__=='__main__':
    audio_url = "X:\\Box\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\media\\AA_9ded1778-0639-4e1b-8051-e4ce3bb3a94e_cons2_audio.m4a"

    audio_path = '/mnt/x/Box Sync/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media/AA_029afeb8-cf16-468f-9d86-2f79ad8978ee_cons2_audio.m4a'

    transform_to_wav(audio_path, 'wav_copy.wav')
