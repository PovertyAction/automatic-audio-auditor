# Training starting from raw surveyCTO audios

## Building training set

### Data transformation

surveyCTO media are .mp4a 8khz 30 minute long audios. Deepspeech works with .wav 16khz ~10 second audios for training. So significant transformation has happen first

Run:

`data_transformation.py`

For the moment audio_url and audio segmentation agressivenes is hardcoded.

`data_transformation.py` needs ffmpeg installes

`apt-get install ffmpeg libavcodec-extra`.

In addition, it uses `vad_transcriber` from DeepSpeech-examples repo. So import those too.


### Building trains.csv, dev.csv and test.csv

[PENDING]

Check out DeepSpeech documentation to learn how these files should be.

## Training your model with your ready datasets

Check README.md in training folder.
