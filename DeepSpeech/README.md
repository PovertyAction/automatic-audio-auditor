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

### Setup

Follow instructions on:
https://deepspeech.readthedocs.io/en/latest/TRAINING.html

Additionally, consider using following commands:

`pip3 install --no-use-pep517 --upgrade -e .` instead of `pip3 install --upgrade -e .`

At some point you might get a sox error. Fix it with

`sudo apt-get install sox libsox-fmt-mp3`

Once you have everything set up according to the instructions, run the following command from your virtual env to train:

[Here working for my computer, fix routes so that it works for you]

Spanish:
```
python3 -u DeepSpeech.py \
  --train_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/data/colombia/train.csv \
  --dev_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/data/colombia/dev.csv \
  --test_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/data/colombia/test.csv \
  --train_batch_size 1 \
  --dev_batch_size 1 \
  --test_batch_size 1 \
  --load_cudnn true \
  --epochs 3 \
  --checkpoint_dir  /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/checkpoint/cclmtv \
  --learning_rate 0.0001 \
  --alphabet_config_path ../deepspeech-polyglot/data/alphabet_es.txt
  <!-- --load_evaluate last -->
```

English:
```
python3 -u DeepSpeech.py \
  --train_files data/ldc93s1/ldc93s1.csv \
  --dev_files data/ldc93s1/prueba_dev.csv
  --test_files data/ldc93s1/prueba_test.csv \
  --train_batch_size 1 \
  --dev_batch_size 1 \
  --test_batch_size 1 \
  --n_hidden 2048 \
  --load_cudnn true \
  --epochs 3 \
  --checkpoint_dir  /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/0.9.3/deepspeech-0.9.3-checkpoint/ \
  --learning_rate 0.0001 \
  <!-- --load_evaluate last -->
```


Resources still to check:
On resampling
https://discourse.mozilla.org/t/inference-with-model-different-than-16khz/43217/23

On fine tuning
https://discourse.mozilla.org/t/links-to-pretrained-models/62688/21

Might be useful:
https://discourse.mozilla.org/t/training-model-for-fluently-spoken-language/43571/3
