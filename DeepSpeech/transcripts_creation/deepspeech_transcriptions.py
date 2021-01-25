# python3 audioTranscript_cmd.py --aggressive 3 --audio ~/deepspeech-adventures/audio/spanish_transcript.wav --model ~/deepspeech-adventures/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/only\ models/


from os import path
import sys
sys.path.append(path.abspath('../../../DeepSpeech-examples'))
sys.path.append(path.abspath('../../../DeepSpeech-examples/vad_transcriber'))

from vad_transcriber import audioTranscript_cmd


audioTranscript_cmd.main(sys.argv[1:])


# python3 deepspeech_transcriptions.py --aggressive 3 --audio ./audio/spanish_transcript.wav --model .//models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/only\ models
