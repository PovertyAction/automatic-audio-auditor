# Reference: https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/get-started-speech-to-text?tabs=script%2Cwindowsinstall&pivots=programming-language-python
import azure.cognitiveservices.speech as speechsdk
import time
from .azure_keys import get_speech_key, get_service_region
import json
#Parameters
speech_key = get_speech_key()
service_region = get_service_region()

def get_speech_config_properties():
    print("Properties:")
    for a in speechsdk.PropertyId:
        print(a)

def set_initital_silenece_timeout(speech_config, timeout):
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, timeout)

def recognize_once(speech_recognizer):
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(result.no_match_details))
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

def print_if_debugging(text, show_debugging_prints):
    if show_debugging_prints:
        print(text)

#Global to indicate when transcription is done
done = None

def generate_transcript(file_path, language, return_list = True, show_debugging_prints=False):
    global done
    done = False

    #Set SpeechConfig, AudioConfig and SpeedRecognizer
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    speech_config.speech_recognition_language=language
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    audio_config = speechsdk.audio.AudioConfig(filename=file_path)

    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    #Method triggered when transcription is finished
    def stop_cb(evt):
        global done
        print_if_debugging('CLOSING on {}'.format(evt), show_debugging_prints)
        speech_recognizer.stop_continuous_recognition()
        done = True

    #List saving all pieces of recognized text
    recognized_text = []
    def save_recognized_text(evt):
        print_if_debugging('RECOGNIZED: {}'.format(evt), show_debugging_prints)
        if(evt.result.text!=""):
            lexical_text = json.loads(evt.result.json)['NBest'][0]['Lexical']
            recognized_text.append(lexical_text)

    #We connect callbacks to eventrs from the speech_recognizer
    speech_recognizer.recognized.connect(lambda evt: save_recognized_text(evt))
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    #For other callbacks:
    # speech_recognizer.recognizing.connect(lambda evt: print_if_debugging('RECOGNIZING: {}'.format(evt)))
    speech_recognizer.session_started.connect(lambda evt: print_if_debugging('SESSION STARTED: {}'.format(evt), show_debugging_prints))
    speech_recognizer.session_stopped.connect(lambda evt: print_if_debugging('SESSION STOPPED {}'.format(evt), show_debugging_prints))
    speech_recognizer.canceled.connect(lambda evt: print_if_debugging('CANCELED {}'.format(evt), show_debugging_prints))

    #Start continuous recognition
    speech_recognizer.start_continuous_recognition()

    #We want to keep listening to events untils the speech_recognizer session_stopped event is triggered
    while not done:
        time.sleep(0.5)

    full_transcript = recognized_text
    print_if_debugging(full_transcript, show_debugging_prints)

    if return_list:
        return full_transcript
    else:
        return " ".join(full_transcript)

if __name__ == '__main__':

    get_speech_config_properties()
