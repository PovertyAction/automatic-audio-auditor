
# Automatic Audio Auditor (AAA)

## Project description

To assure data quality during our field and phone surveys, IPA audits recorded responses manually to detect that quality standards are met, such as consents fully read, surveys delivered completely, and how respondents answer questions. However, manual audits are expensive and not scalable. This scenario provides an opportunity to leverage the existing survey data and machine learning capabilities to develop a tool that automatically analyzes the audio recordings, potentially in real time, and flags survey responses that need revision and enumerators that need additional training.

The Automatic Audio Auditor (AAA) is a system that automatically audits survey audio recordings and flags enumerators and question items that present evidence of low quality. The system generates transcripts of audio recordings using machine learning transcription models, and then compares the transcripts to survey questionnaires to identify: if consents were read appropriately, if all questions were asked, and if respondents' answers were the same as the ones recorded in the survey platform.

In the recent months we have developed a proof of concept version of the automatic audio auditor tool. Code is available in this repo. In order to generate audio transcripts, we use Azure Cognitive Services speech-to-text engine, which accurately generates transcripts in a variety of languages and accents. In addition, we are using our own transcription models using Mozilla Deepspeech, in particular to deploy them in contexts with no internet connectivity. In order to identify if consent scripts and questions are present, we compute distance metrics between the transcripts and the questionnaire's scripts.

The main outputs of the system are an enumerator-level report, indicating which enumerators had the most significant amount of flagged survey-responses, and a question-level analysis, which signals which questions were not properly read or missing.

To begin with, the Automatic Audio Auditor will supplement manual audits and help to target surveys that require additional analysis. In subsequent versions we plan to build more complex capabilities into the tool, such as functionality to evaluate tone or identify probing, and the potential for real-time analysis and data quality input to enumerators. We also plan to use this tool to develop a library of voice samples across the multiple languages with which we interact. Such samples would be used to train our ML models, as well as for comparative research.

## Product development plans

This project is under development: we are still heavily working on it and testing it.

Next Steps in developing the project:
- Find more precise ways of identifying where questions are present in audio recordings. For the moment we are relying on text audits (and soon advanced text audits - eventlogs), but there could be other strategies to think about.
- When comparing transcript to questionnaire, consider best way to detect differences. Maybe we would only like to check if some key words are present, for example.
- Continue developing an Azure Cognitive Services based application, particularly one that works with generation of batch transcriptions
- Develop an offline DeepSpeech based solution. Possibly build training sets with local languages for training. Train transcription models and fine tune
- Manually create transcripts so as to check if automatic transcript generator works well
- Study transcript engine performance in different languages and contexts
- Scale up the solution and design a system to offer the service to all country offices.
- Testing system on field surveys data, in contrast to phone survey data
- Design other ways to detect data quality issues apart from current checks (for example,  detecting probing, identification of speakers, considering amount of background noise, amount of people speaking, tone, etc)
- Considering transcription model biases and variance in performance for different contexts

## Files in the repo

* audio_auditor.py: Main system scripts. Launches one of the following tasks: create transcription tasks, upload transcript audio files, launch transcription tasks, receives transcriptions from Azure, analyze transcription and creates reports.
* transcript_generator.py: Creates transcripts, currently with Azure Cognitive Services (invokes Azure/*.py scripts)
* db_manager.py: Manages projects data, currently saved in .json files for fast prototyping
* text_differences.py: Computes measures of differences between transcripts and questionnaires
* questionnaire_texts.py: To extract questions scripts from questionnaires.
* aa_params.py: Parameters for the audio auditor depending on the project (So far only implemented for RD1 and RD3 of COL RECOVR project)
* report_generation.py: Creates .xlsx reports based on the analysis
* outputs_writer.py: Functions to save outputs
* DeepSpeech/*.py scripts: All functionality for using and training DeepSpeech models.

## Setup

To install all dependencies, run 

`pip -r install requirements.txt`

Its recommended to do this after activating a virtual environment. To set up one in Linux:

Create a python virtual env:

`python3 -m venv venv`

(Install python3 venv if you dont have it with `sudo apt-get install python3-venv`)

Activate venv

`source venv/bin/activate`

### Azure keys

Add the file `azure_keys.py` in the Azure folder.

# How to run

`python audio_auditor --project_id your_project_id --task_id chosen_task_id --os_id os_id`

Example:
`python audio_auditor.py --project_id 1 --task_id 1 --os_id 2`

Project ids:
RECOVER_RD3_COL: 1

Tasks ids:
1:CREATE_TRANSCRIPTION_TASKS
2:UPLOAD_TRANSCRIPT_AUDIO_FILES
3:LAUNCH_TRANSCRIPT_TASKS
4:RECEIVE_AZURE_BATCH_TRANSCRIPTIONS
5:LIVE_TRANSCRIPTIONS
6:ANALYZE_TRANSCRIPTS
7:CREATE_REPORTS

Operating systems:
'windows': 1
'linux': 2
