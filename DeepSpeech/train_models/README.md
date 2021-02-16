### Setup

Follow instructions on:
https://deepspeech.readthedocs.io/en/latest/TRAINING.html

Additionally, consider using following commands:

`pip3 install --no-use-pep517 --upgrade -e .` instead of `pip3 install --upgrade -e .`

At some point you might get a sox error. Fix it with

`sudo apt-get install sox libsox-fmt-mp3`

Once you have everything set up according to the instructions, run the following command from your virtual env to train:

[Here working for my computer, fix routes so that it works for you]

`source deepspeech-venv/bin/activate`

Spanish:

Training
```
python3 -u DeepSpeech.py \
  --train_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/RECOVER-RD3-COL/train.csv \
  --dev_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/RECOVER-RD3-COLdev.csv \
  --train_batch_size 1 \
  --dev_batch_size 1 \
  --load_cudnn true \
  --epochs 3 \
  --load_checkpoint_dir /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/original/cclmtv \
  --save_checkpoint_dir /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/colombia-checkpoint \
  --learning_rate 0.0001 \
  --alphabet_config_path ../deepspeech-polyglot/data/alphabet_es.txt
```
Testing
```
python3 -u DeepSpeech.py \
  --test_files /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/training_data/RECOVER-RD3-COL/test.csv \
  --test_batch_size 1 \
  --load_cudnn true \
  --epochs 3 \
  --learning_rate 0.0001 \
  --alphabet_config_path ../deepspeech-polyglot/data/alphabet_es.txt \
  --load_checkpoint_dir /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/colombia-checkpoint
  or
  --load_checkpoint_dir /mnt/c/Users/felip/ml_for_survey_data_quality/DeepSpeech/models/DeepSpeech-Ployglot-ES-20201026T155049Z-001/original/cclmtv
 ```

//

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
