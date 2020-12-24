# Running code

`python3 deepspeech_transcriptions.py --aggressive 1 --audio ./audio/spanish_transcript.wav --model ./models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/only\ models`

# Setup

## Downloading transcriber for long wav files

The Deepspeech-examples repo has an example that transcribes long wav files, so we will use that. Nonetheless, it has some missing features that we need, so rather than using the original repo, we will use a fork that has the necessary fixes.

`git clone Deepspeech-examples from https://github.com/fhalamos/DeepSpeech-examples/tree/vad_transcriber_updates`

## Setting up project

```
cd audio_auditor/DeepSpeech

#Once
virtualenv -p python3 ./deepspeech-venv/

source ./deepspeech-venv/bin/activate

pip3 install -r requirements.txt
```

## Downloading models

I downloaded the spanish models from https://gitlab.com/Jaco-Assistant/deepspeech-polyglot

There you can find other pre trained models for other languages (at the very bottom of the page).

The english models can be found in DeepSpeech repo.
