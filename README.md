# Project description

The automatic audio auditor is a tool that analyzes audio audits, looking for evidence of quality issues in survey responses.

For each survey response, the system will check if all answers were read appropriately by surveyors, and if answers given by respondents were correctly written down in surveycto. In order to do that, we use text audits to learn where is each question located in the audio recording, and then use transcription engines to generate the transcript of a given question. Finally, we compare the transcripts with questionnaires and surveycto response.

Project under development, still heavily working on it and testing it.
For a presentation with a bit more of explanation, click [here](https://docs.google.com/presentation/d/14f1rY_T2rvSmksRUGsXT4RET9nRp2kZc6SfklaUdKP0/edit?usp=sharing)

# Files in repo

## Core of the code:

* audio_auditor.py: Main logic of the system. Loads all files, checks questions and answers.
* transcript_generator.py: Creates transcripts, currently with Azure Cognitive Services
* azure_transcribe.py: For use of Azure Cognitive Services
* text_differences.py: Computes measures of differences between transcripts and questionnaires
* questionnaire_texts.py: To extract questions scripts from questionnaires.
* aa_params.py: Parameters for the audio auditor depending on the project (So far only implemented for RD1 and RD3 of COL RECOVR)

## Audio_auditor architechture

(Referencing audio_auditor.py here)

Currently we are using an OOP design to model the different components of the audio auditor. We are currently evaluating this design, its not ideal nor very clean.

The main classes are:

* AudioAuditor: main class, in charge of loading files and running high level analysis
* SurveyEntrieAnalyzer: runs the analysis for each survey entry (a full survey response), using a QuestionAnalyzer instance for each question.
* QuestionAnalyzer: runs the analysis for only one question, checking question script and answer (using AnswerAnalyzer for this last task).
* AnswerAnalyzer: focuses in checking if surveycto answer matches with answer found in transcript.

<!-- # DeepSearch

https://deepspeech.readthedocs.io/en/v0.8.2/?badge=latest

deepspeech --model DeepSpeech-Ployglot-ES/output_graph_es.pbmm --scorer DeepSpeech-Ployglot-ES/kenlm_es.scorer --audio transcript.wav -->
