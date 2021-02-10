import os
import pandas as pd
import numpy as np
import string
import sys
import json

import transcript_generator
import text_differences
import questionnaire_texts
import aa_params

import time
from num2words import num2words
from text_to_num import alpha2digit

from outputs_writer import save_df_to_excel
import db_manager
import report_generation

#Some string constants used along the code
FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'
FULL_SURVEY = 'full_survey'
TEXT_AUDIT = 'text_audit'

transcripts_cache = None
TRANSCRIPTS_CACHE_FILE_NAME = 'transcripts_cache.json'

transcript_tasks_db = None
TRANSCRIPT_TASKS_DB_FILE_NAME = 'transcript_tasks_db.json'

question_analysis_db = None
QUESTION_ANALYSIS_DB_FILE_NAME = 'question_analysis_db.json'

debugging = False
def print_if_debugging(text):
    if debugging:
        print(text)

def get_yes_keywords(full_language):
    '''
    Depending on language, return all words that relate to 'yes'
    '''
#--->Should move this function to a separate file
    language = full_language.split('-')[0]
    if language == 'es':
        return ['si','sí','bueno','ok', 'estoy de acuerdo', 'estoy deacuardo']
    elif language == 'en':
        return ['yes', 'ok']
    else:
        return None


def amount_of_words(phrase):
    if phrase:
        return len(phrase.split(' '))
    else:
        return False

def seconds_to_nice_format(time_in_seconds):
    time_nice_format = time.strftime('%M:%S', time.gmtime(time_in_seconds))
    return time_nice_format

def remove_accents(word):
    for a,b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u')]:
        word = word.replace(a,b)
    return word

def remove_punctuations(word):
    no_punctuations = word.translate(str.maketrans('', '', string.punctuation))
    for char in ['?','¿','!','¡']:
        no_punctuations = no_punctuations.replace(char,"")

    return no_punctuations

def import_data(dataset_path):
  if dataset_path.endswith('dta'):

    #We might want to do conver_categoricals=True to directly compare transcript answers with surveycto answers
    dataset = pd.read_stata(dataset_path, convert_categoricals=False)

    label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
    try:
        value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
    except AttributeError:
        status_message = "No value labels detected."
        value_label_dict = None

    return dataset, label_dict, value_label_dict



class AnswerAnalyzer:
    def __init__(self, q_analyzer):
        self.q_analyzer = q_analyzer

        #Questions transcripts are a list of phrases.
        #By default, we assume that responses come in the last phrase of the transcript
        #Nonetheless, it sometimes happens that last phrase its just a confirmation of the surveyor after the respondents answer.
        #We expect to identify this cases when the last 2 phrases of the transcript are very short
        #Ex: ['Could you tell me if you are happy?', 'Yes', 'Thanks']
        #So, what we will do is to concatenate the 2 last phrases if they are both short.
        #If the last 2 are excesively short, and the 3rd to last is not too long, we include that too.
        #Ex: ['¿Piensa en las 5 mujeres más cercanas a usted, cuántas de ellas cree que piensan que si una mujer siempre quiere controlar a su esposo es una buena razón para su esposo? Les ello.', '¿Las personas no?', 'No.', 'Buen.', 'Oh.']


        def get_last_3_phrases():

            last_phrase = self.q_analyzer.q_transcript[-1]

            if len(self.q_analyzer.q_transcript) == 1:
                second_last_phrase = None
                third_last_phrase = None
            elif len(self.q_analyzer.q_transcript) == 2:
                second_last_phrase = self.q_analyzer.q_transcript[-2]
                third_last_phrase = None
            else:
                second_last_phrase = self.q_analyzer.q_transcript[-2]
                third_last_phrase = self.q_analyzer.q_transcript[-3]
            return third_last_phrase, second_last_phrase, last_phrase
        self.third_last_phrase, self.second_last_phrase, self.last_phrase = get_last_3_phrases()

        def get_transcript_of_answer_only():

            #Default is to use only last phrase
            transcript_of_answer_only = self.last_phrase

            #If last phrase is short, as well as previous two, join them all.
            if self.third_last_phrase and amount_of_words(self.third_last_phrase) <=3 and \
             self.second_last_phrase and amount_of_words(self.second_last_phrase) <=3 and \
             amount_of_words(self.last_phrase) <=3:
                transcript_of_answer_only = " ".join([self.third_last_phrase, self.second_last_phrase, self.last_phrase])

            #If last phrase is short, as well as previous one, join them
            elif self.second_last_phrase and amount_of_words(self.second_last_phrase) <=3 and \
             amount_of_words(self.last_phrase) <=3:
                transcript_of_answer_only = " ".join([self.second_last_phrase, self.last_phrase])

            #if last_phrase is extremelly short, then be more flexible with using latter even if they are longer than 3 (say max 6 words)
            #Ex: ['¿En los últimos 7 días usted realizó alguna otra actividad para generar ingresos o manejò su propio negocio?', 'Pues no porque no tengo nada.', 'Bueno.']
            elif self.second_last_phrase and amount_of_words(self.second_last_phrase) <=6 and \
             amount_of_words(self.last_phrase) == 1:
                transcript_of_answer_only = " ".join([self.second_last_phrase, self.last_phrase])

            #Lastly, we clean transcript of answer so as to remove punctuations and make it more easy to find words
            transcript_of_answer_only = remove_punctuations(transcript_of_answer_only)

            return transcript_of_answer_only
        self.transcript_of_answer_only = get_transcript_of_answer_only()



    def transcript_has_too_many_phrases(self, threshold=5):
        if len(self.q_analyzer.q_transcript)>threshold:
            return True
        else:
            return False

    def last_phrase_too_many_words(self, threshold=5):
        if amount_of_words(self.q_analyzer.q_transcript[-1])>threshold:
            return True
        else:
            return False

    def analyze_select_one_response(self, ):
        #pending.. finding the correct option in transcript looks very tricky
        select_one_type = self.q_analyzer.q_type.split()[1]

        # if select_one_type == 'cov1':
        #     print('***************************************************************\n\n\n\n')
        #     print(self.q_analyzer.q_code)
        #     print(self.q_analyzer.q_type)
        #     print(self.q_analyzer.q_transcript)
        #     print(self.surveycto_answer)

        return None, None

    def analyze_integer_response(self):

        def is_float(s):
            try:
                float(s)
                return True
            except:
                return False

        def is_int(s):
            try:
                int(s)
                return True
            except:
                return False

        if not is_int(self.surveycto_answer):
            return False, f'Surveycto answer not a num: {self.surveycto_answer}'

        #CASE CORRECT INTEGER WAS RECORDED
        #Lets look at last phrase in trascript and see if it has the survey_cto_answer
        #We first check if number in digits is present
        if str(int(self.surveycto_answer)) in self.transcript_of_answer_only:
            return True, f'Found {self.surveycto_answer} in transcript'
        #We then check if number in words is present
        if num2words(self.surveycto_answer, lang='esp') in self.transcript_of_answer_only.lower():
            return True, f"Found {num2words(self.surveycto_answer, lang='esp')} in transcript"

        #We check if words that reprsent 0 are present
        for string_that_represent_cero in ['ningun', 'no']:
            if int(self.surveycto_answer)==0 and \
            string_that_represent_cero in self.transcript_of_answer_only.lower().split(" "):
                return True, f"'{string_that_represent_cero}' is associated to 0 and apppears in response"

        #Try to capture if any number where present as words in question_transcript, and check if its != to the one in surveycto
        #Create list of integers we can find in transcript
        numeric_values_in_transcript = [int(float(alpha2digit(w,"es"))) \
                                    for w in self.transcript_of_answer_only.split(" ") \
                                    if is_float(alpha2digit(w,"es"))]

        #Compare digits found with surveycto answer
        if len(numeric_values_in_transcript)>0:
            if int(self.surveycto_answer)!=numeric_values_in_transcript[-1]:
                return False, f'Value {numeric_values_in_transcript[-1]} detected in answer, different to {int(self.surveycto_answer)}'
            else:
                return True, f'Value {numeric_values_in_transcript[-1]} detected in answer'

        #Check if there is presence of background noise
        if 'background' in self.transcript_of_answer_only.lower().split(" "):
            return None, "background noise in transcription, can't conclude"

        return None, 'Could not conclude'

    def check_yes_no_recorded_in_surveycto(self, yes_or_no):
        #Check if a 'yes' or a 'no' (whatever value comes in the yes_or_no var) is the one saved in surveycto
        if self.surveycto_answer in  self.q_analyzer.survey_entrie_analyzer.audio_auditor.params['survey_cto_yes_no_values'][yes_or_no]:
            return True
        else:
            return False

    def analyze_yes_no_response(self):

        def find_any_of_words_in_text(text, words_to_check):
            #Check if any of the words present in words_to_check can be found in text

            clean_text = remove_accents(text)
            clean_text = remove_punctuations(clean_text)
            clean_text = clean_text.lower()

            #Check if any of the words in the text is part of the words_to_check list
            for text_word in clean_text.split(' '):
                if text_word in words_to_check:
                    return text_word
            return False

        def get_no_strings(language):
            if language=='es':
                return ['no']
            return False

        def get_yes_strings(language):
            if language=='es':
                return ['si', 'correcto']
            return False

        #Correct answer imputed
        #Check a 'yes' was written in surveycto and found in transcript, or
        #Check a 'no' was written in surveycto and found in transcript

#--->Variable names here are horrible, need to change this
        for yes_or_no, get_yes_no_strings in [('yes', get_yes_strings),('no', get_no_strings)]:
            if self.check_yes_no_recorded_in_surveycto(yes_or_no):
                yes_no_word_found = find_any_of_words_in_text(self.transcript_of_answer_only, get_yes_no_strings(language='es'))
                if yes_no_word_found:
                    return True, f"'{yes_no_word_found}' found in transcript"


        #Wrong answer imputed
        for yes_or_no, get_yes_no_strings in [('yes', get_no_strings),('no', get_yes_strings)]:
            if self.check_yes_no_recorded_in_surveycto(yes_or_no):
                yes_no_word_found = find_any_of_words_in_text(self.transcript_of_answer_only, get_yes_no_strings(language='es'))
                if yes_no_word_found:
                    return False, f"'{yes_no_word_found}' found in transcript, but surveycto answer is {yes_or_no}"

        return None, 'Not being able to recognize answer for YES/NO question'

    def get_surveycto_answer(self):

        #Check that question code is in survey df
        if self.q_analyzer.q_code in self.q_analyzer.survey_entrie_analyzer.survey_row:
            return self.q_analyzer.survey_entrie_analyzer.survey_row[self.q_analyzer.q_code]
        else:
            return None
    def check_answer_given_matches_surveycto(self):


        self.surveycto_answer = self.get_surveycto_answer()
        print_if_debugging(f'surveycto_answer {self.surveycto_answer}')

        #If the amount of words in last phrase is too long, then we might be capturing the enumerator speaking and not the responden (we are missing the last interaction
        if self.last_phrase_too_many_words():
            return None, 'Last phrase in transcript contains too many words, so most probably its the enumerator speaking, aka, we couldnt capture respondent'

        #If the question_transcript has too many phrases, it might be the case this questions contains other subquestions all toqueter (fsec3-fsec7 for example), and hence, the text_audit does not separate them, we cant do the answer analysis
        if self.transcript_has_too_many_phrases():
            return None, 'Transcript has too many phrases: there might to many back and forths or more than one question/answer here'

        if self.q_analyzer.q_type == 'integer':
            response, reason = self.analyze_integer_response()

        elif self.q_analyzer.q_type in self.q_analyzer.survey_entrie_analyzer.audio_auditor.params['yes_no_question_types']:
            response, reason = self.analyze_yes_no_response()

        # elif self.q_analyzer.q_type.split()[0] == 'select_one':
        #     response, reason = self.analyze_select_one_response()

        else:
            response, reason = None, f'{self.q_analyzer.q_type} not supported for answer analysis'

        return response, reason




def compute_offset_and_duration(ta_row, first_q_offset=0, previous_ta_row=None, next_ta_row=None):
    q_first_appeared = ta_row['First appeared (seconds into survey)']-first_q_offset

    #Sometimes duration is longer than it should (given back and forths), so we will choose duration = difference between next q starting point and current one, if duration reported is too long.
    q_duration = ta_row['Total duration (seconds)']

    if next_ta_row is not None:
        next_q_first_appeared = next_ta_row['First appeared (seconds into survey)']-first_q_offset

        if next_q_first_appeared-q_first_appeared<q_duration and next_q_first_appeared!=q_first_appeared: #Be sure they dont have the same starting point (grouped questions)
            q_duration = next_q_first_appeared-q_first_appeared

    return q_first_appeared, q_duration+1

class QuestionAnalyzer:
    def __init__(self, survey_entrie_analyzer, ta_row, previous_ta_row=None, next_ta_row=None):
        self.ta_row = ta_row
        self.previous_ta_row = previous_ta_row
        self.next_ta_row = next_ta_row
        self.survey_entrie_analyzer = survey_entrie_analyzer

        #Get question name, code, type, script
        q_full_name = self.ta_row['Field name']
        self.q_code = q_full_name.split('/')[-1]

        self.q_type = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'type')

        #Check if current question is a repeated question (cause its in a repeat group)
        if (self.previous_ta_row is not None and self.q_code == self.previous_ta_row['Field name'].split('/')[-1]) or \
           (self.next_ta_row is not None and self.q_code == self.next_ta_row['Field name'].split('/')[-1]) :
            self.repeate_group_q = True
            self.survey_entrie_analyzer.increase_q_repetition(self.q_code)
            self.repeated_q_number = self.survey_entrie_analyzer.repetitions_counter[self.q_code]
        else:
            self.repeate_group_q = False
            self.repeated_q_number = 0

        #Get question script
        self.q_script = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'label:spanish')

    def create_response_dict(self, answer_analyzer):
        response = {}
        response['enum_id'] = self.survey_entrie_analyzer.enumerator_id
        response['case_id'] = self.survey_entrie_analyzer.case_id
        response['question'] = self.q_code
        response['time_in_audio'] = \
            f'{seconds_to_nice_format(self.q_first_appeared)}-{seconds_to_nice_format(self.q_first_appeared+self.q_duration)}'
        response['question_missing'] = self.q_missing
        response['read_inappropiately'] = self.q_read_inappropiately

        # if response['read_appropiately'] is False:
        response['perc_script_missing'] = self.perc_script_missing
        response['q_words_missing'] = self.words_missing
        response['q_script'] = self.q_script
        response['transcript'] = self.q_transcript
        response['answer_matches_surveycto'] = answer_analyzer.answer_matches_surveycto
        response['reason_for_match'] = answer_analyzer.reason_for_match
        response['surveycto_answer'] = answer_analyzer.surveycto_answer
        response['audio_path'] = self.survey_entrie_analyzer.audio_path.split("\\")[-1]
        response['textaudit_path'] = self.survey_entrie_analyzer.text_audit_path.split("\\")[-1]

        return response

    def analyze_question_transcript(self, read_appropiately_threshold=0.4, read_appropiately_threshold_short_questions=0.55, question_missing_threshold=0.8):

        if not self.acceptable_question_type():
            return None

        if not self.question_has_script():
            return None

        #If question is already analyzed, skip
        if db_manager.get_element_from_database(
            database = question_analysis_db,
            project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
            case_id = self.survey_entrie_analyzer.case_id,
            q_code = self.q_code,
            repeate_group_q = self.repeate_group_q,
            repeated_q_number = self.repeated_q_number) is not None:
            print(f"!!Analysis found for {self.survey_entrie_analyzer.audio_auditor.params['project_name']} {self.survey_entrie_analyzer.case_id} {self.q_code}.")
            return None

        #Get question transcript
        self.q_transcript = db_manager.get_element_from_database(
            database = transcripts_cache,
            project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
            case_id = self.survey_entrie_analyzer.case_id,
            q_code = self.q_code,
            repeate_group_q = self.repeate_group_q,
            repeated_q_number = self.repeated_q_number)

        if not self.q_transcript:
            print_if_debugging(f'Couldnt find transcript in transcrips database for {self.q_code}')
            return False

        #Get % of script that was actually pronounced
        full_transcript = " ".join(self.q_transcript)
        self.perc_script_missing, self.words_missing = text_differences.compute_perc_script_missing(self.q_script, self.q_transcript, self.survey_entrie_analyzer.audio_auditor.params['language'])

        #Question is read appropiately as long as the percentage of words missing from script is lower than thrshold.
        #For very short question scripts (below 4 words), we reduce threshold
        if len(self.q_script.split(" "))<=3:
            read_appropiately_threshold = read_appropiately_threshold_short_questions
        self.q_read_inappropiately = self.perc_script_missing>read_appropiately_threshold
        self.q_missing = self.perc_script_missing > question_missing_threshold

        #Compare recorded response with surveycto saved response
        answer_analyzer = AnswerAnalyzer(self)
        answer_analyzer.answer_matches_surveycto, answer_analyzer.reason_for_match = answer_analyzer.check_answer_given_matches_surveycto()

        #Getting this again just to inlcude it in response
        self.q_first_appeared, self.q_duration = transcript_generator.get_first_appeared_and_duration(
        ta_row=self.ta_row, previous_ta_row=self.previous_ta_row, first_q_offset= self.survey_entrie_analyzer.start_recording_ta_offset)

        #Prepare response dict
        response = self.create_response_dict(answer_analyzer)

        return response


    def acceptable_question_type(self):
        #Do not check notes nor checkpoints
        if  self.q_type == 'note' or 'checkpoint' in self.q_code:
            # print_if_debugging(f'Skipping question type {self.q_type}\n')
            #Tell the transcript_generator to forget previous_transcript
            # transcript_generator.previous_transcript_to_none()
            return False
        else:
            return True

    def question_has_script(self):
        if not self.q_script:
            print_if_debugging(f"Didnt find question script for {self.q_code}")
            return False
        if len(self.q_script.replace(" ", ""))==0:
            print_if_debugging(f"No question script (usually question contianed only instructions for surveyor) for {self.q_code}")
            return False

        return True

    def create_transcript_task(self):

        if not self.acceptable_question_type():
            return

        if not self.question_has_script():
            return

        #If transcript already exists, do not create task
        if db_manager.get_element_from_database(
            database = transcripts_cache,
            project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
            case_id = self.survey_entrie_analyzer.case_id,
            q_code = self.q_code,
            repeate_group_q = self.repeate_group_q,
            repeated_q_number = self.repeated_q_number) is not None:
            print(f">>>Transcript found for {self.survey_entrie_analyzer.audio_auditor.params['project_name']} {self.survey_entrie_analyzer.case_id} {self.q_code}")
            return

        #If task already exists, do not create it
        if db_manager.get_element_from_database(
            database = transcript_tasks_db,
            project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
            case_id = self.survey_entrie_analyzer.case_id,
            q_code = self.q_code,
            repeate_group_q = self.repeate_group_q,
            repeated_q_number = self.repeated_q_number) is not None:
            print(f"<<<<Transcript task found for {self.survey_entrie_analyzer.audio_auditor.params['project_name']} {self.survey_entrie_analyzer.case_id} {self.q_code}")
            return

        #Compute offset and duration
        offset, duration = compute_offset_and_duration(
            ta_row = self.ta_row,
            first_q_offset= self.survey_entrie_analyzer.start_recording_ta_offset,
            previous_ta_row= self.previous_ta_row,
            next_ta_row = self.next_ta_row)

        task_info = {
            'audio_url':self.survey_entrie_analyzer.audio_path,
            'language':self.survey_entrie_analyzer.audio_auditor.params['language'],
            'offset':int(offset),
            'duration':int(duration)
            }

        db_manager.save_to_db(
            database = transcript_tasks_db,
            database_file_name = TRANSCRIPT_TASKS_DB_FILE_NAME,
            project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
            case_id = self.survey_entrie_analyzer.case_id,
            q_code = self.q_code,
            repeate_group_q = self.repeate_group_q,
            repeated_q_number = self.repeated_q_number,
            element_to_save=task_info)
        print(f"*** Created transcript task for {self.survey_entrie_analyzer.audio_auditor.params['project_name']} {self.survey_entrie_analyzer.case_id} {self.q_code}")


class SurveyEntrieAnalyzer:
    def __init__(self, audio_auditor, survey_row):
        self.survey_row = survey_row
        self.audio_auditor = audio_auditor
        self.case_id = self.survey_row[audio_auditor.params['col_case_id']]
        self.audio_path = self.get_media_file_path(file_to_get = FULL_SURVEY)
        self.text_audit_df = self.get_text_audit_df()
        self.enumerator_id = self.survey_row[audio_auditor.params['col_enumerator_id']]

        #To keep count of repeated questions
        self.repetitions_counter = {}


        #Text audit capture segments of the interview that are not recorded, particularly the first ones that has surveycto metadata
        #We need to learn when does the recording start, and ends, relative to the beggining of the text audit
        self.start_recording_ta_index, self.start_recording_ta_offset = self.get_when_recording_starts()
        self.last_question_index = self.get_last_question_index()

    def increase_q_repetition(self, q_code):
        if q_code not in self.repetitions_counter:
            self.repetitions_counter[q_code] = 1
        else:
            self.repetitions_counter[q_code] +=1

    def get_when_recording_starts(self):
        q_when_recording_starts_df = self.text_audit_df.loc[self.text_audit_df['Field name'] == self.audio_auditor.params['q_when_recording_starts']]
        start_recording_ta_index = int(q_when_recording_starts_df.index[0])
        start_recording_ta_offset = int(q_when_recording_starts_df['First appeared (seconds into survey)'].iloc[0])
        return start_recording_ta_index, start_recording_ta_offset

    def audio_path_exists(self):
        if(not self.audio_path):
            print_if_debugging("No audio_path")
            return False

        #Check audio exists
        if not os.path.exists(self.audio_path):
            print_if_debugging(f"Audio {self.audio_path} does not exist")
            return False

        return True

    def get_text_audit_df(self):

        self.text_audit_path = self.get_media_file_path(file_to_get = TEXT_AUDIT)


        #open in universal-new-line mode, according to https://github.com/pandas-dev/pandas/issues/11166
        text_audit_df = pd.read_csv(open(self.text_audit_path,'rU'), encoding='utf-8', engine='c')
        # text_audit_df = pd.read_csv(self.text_audit_path)

        return text_audit_df

    def get_last_question_index(self):
        last_q_df = self.text_audit_df.loc[self.text_audit_df['Field name'] == self.audio_auditor.params['last_question']]
        last_question_index = int(last_q_df.index[0])
        return last_question_index

    def get_media_file_path(self, file_to_get):

        if(file_to_get == FULL_SURVEY):
            path = self.survey_row[self.audio_auditor.params['col_full_survey_audio_audit_path']]

        elif(file_to_get == TEXT_AUDIT):
            path = self.survey_row[self.audio_auditor.params['col_text_audit_path']]

        #Return False if path is empty
        if path=='':
            return False

        #Path at the moment has format:
        #media\\AA_001df0ef-acdb-4228-8686-9137d8ae0e27-audio_audit_cons_c_call_phone.m4a'
        #Remove media\\ and add directory
        path_cleaned = path.split('\\')[1]

        full_path = os.path.join(self.audio_auditor.params['media_folder_path'], path_cleaned)

        return full_path



    def print_survey_info(self):
        print("********************************************************************")
        print(f"case_id {self.survey_row[self.audio_auditor.params['col_case_id']]}")
        print(f"Text_audit {self.survey_row[self.audio_auditor.params['col_text_audit_path']]}")#
        # print(f"Firt consent {self.survey_row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH]}")
        # print(f"Second consent {self.survey_row[COL_SECOND_CONSENT_AUDIO_AUDIT_PATH]}")
        print(f"Full survey {self.survey_row[self.audio_auditor.params['col_full_survey_audio_audit_path']]}")
        print("********************************************************************")


    def analyze_survey_transcript(self):

        #Now we analyze each question, looping over the text audit entries
        q_results = []
        # previous_ta_row = None
        # next_ta_row = None
        for index, ta_row in self.text_audit_df.iterrows():

            #Skip initial part of text audit which are not related to questions
            if(index<self.start_recording_ta_index or index > self.last_question_index):
                continue

            # next_ta_row = self.text_audit_df.iloc[index+1]
            q_analyzer = QuestionAnalyzer(self, ta_row)
            q_analysis_result = q_analyzer.analyze_question_transcript()
            if q_analysis_result:
                db_manager.save_to_db(
                    database=question_analysis_db,
                    database_file_name=QUESTION_ANALYSIS_DB_FILE_NAME,
                    project_name = self.audio_auditor.params['project_name'],
                    case_id = self.case_id,
                    q_code = q_analyzer.q_code,
                    repeate_group_q = q_analyzer.repeate_group_q,
                    repeated_q_number = q_analyzer.repeated_q_number,
                    element_to_save = q_analysis_result)



    def create_transcript_tasks(self):

        if not self.audio_path_exists():
            return False

        #Now we create transcriptio task for each question, looping over the text audit entries
        q_results = []
        previous_ta_row = None
        next_ta_row = None
        for index, ta_row in self.text_audit_df.iterrows():

            #Skip initial part of text audit which are not related to questions
            if(index<self.start_recording_ta_index or index > self.last_question_index):
                continue

            next_ta_row = self.text_audit_df.iloc[index+1]

            q_analyzer = QuestionAnalyzer(self, ta_row, previous_ta_row, next_ta_row)
            q_analyzer.create_transcript_task()


class AudioAuditor:
    def __init__(self, name, operating_system):
        self.params = aa_params.get_project_params(name, operating_system)

        #Load survey data
        surveys_df, self.survey_label_dict, self.survey_value_label_dict = import_data(self.params['survey_df_path'])

        #Loas questionnaire
        self.questionnaire_df = pd.read_excel(self.params['questionnaire_path'])

        #Get survey attempts that where completed
        def get_completed_surveys(surveys_df):

            #Filter to get only completed surveys
            completed_surveys_df = surveys_df[surveys_df[self.params['col_survey_status']]==self.params['string_completed_survey']]

            #Filter to get surveys with submissiondates after launch day
            if self.params['project_name'] == 'RECOVER_RD3_COL':
                completed_surveys_df = completed_surveys_df[completed_surveys_df['versionform']>='2011172035']

            return completed_surveys_df
        self.completed_surveys_df = get_completed_surveys(surveys_df)

        #Filter completed_surveys_df to leave only cases id that were selected for analysis (if no selection made, all will be analyzed)
        def filter_completed_surveys_to_only_selected_cases():

            #If no specific list of cases for analysis was given, do nothing, we will analyze all of them
            if 'cases_to_check' not in self.params:
                return
            else:
                #Filter according to case id
                selected_cases_ids = self.params['cases_to_check']
                self.completed_surveys_df = self.completed_surveys_df[self.completed_surveys_df[self.params['col_case_id']].isin(selected_cases_ids)]
        filter_completed_surveys_to_only_selected_cases()

        def sort_surveys_by_case_id_and_reset_index():
            self.completed_surveys_df = self.completed_surveys_df.sort_values(by=['caseid'])
            self.completed_surveys_df.reset_index(drop=True, inplace=True)
        sort_surveys_by_case_id_and_reset_index()

        self.n_rows_to_process = self.completed_surveys_df.shape[0]

    def create_all_surveys_transcript_tasks(self):
        '''
        Creates transcript tasks for questions that have no transcripts yet
        '''
        #Load transcripts cache
        global transcripts_cache
        transcripts_cache = db_manager.load_database(TRANSCRIPTS_CACHE_FILE_NAME)

        #Load transcripts tasks
        global transcript_tasks_db
        transcript_tasks_db = db_manager.load_database(TRANSCRIPT_TASKS_DB_FILE_NAME)


        #Analyze each survey
        for index, survey_row in self.completed_surveys_df.head(self.n_rows_to_process).iterrows():

            print('')
            print(f"SURVEY {index}/{self.n_rows_to_process}. Caseid {survey_row['caseid']}")

            survey_response_analyzer = SurveyEntrieAnalyzer(self, survey_row)
            survey_response_analyzer.create_transcript_tasks()

    def analyze_all_survey_transcripts(self):
        '''
        Runs audits given transcripts are already created
        '''
        #Load transcripts cache
        global transcripts_cache
        transcripts_cache = db_manager.load_database(TRANSCRIPTS_CACHE_FILE_NAME)

        #Load q analysis results db
        global question_analysis_db
        question_analysis_db = db_manager.load_database(QUESTION_ANALYSIS_DB_FILE_NAME)

        for index, survey_row in self.completed_surveys_df.head(self.n_rows_to_process).iterrows():

            print('')
            print(f"SURVEY {index}/{self.n_rows_to_process}. Caseid {survey_row['caseid']}")

            survey_response_analyzer = SurveyEntrieAnalyzer(self, survey_row)
            survey_response_analyzer.analyze_survey_transcript()

if __name__=='__main__':

    projects_ids_to_names = {'1':'RECOVER_RD1_COL','3':'RECOVER_RD3_COL'}

    tasks = {
        '1':'CREATE_TRANSCRIPTION_TASKS',
        '2':'LAUNCH_TRANSCRIPT_TASKS',
        '3':'RECEIVE_AZURE_BATCH_TRANSCRIPTIONS',
        '4':'ANALYZE_TRANSCRIPTS',
        '5':'CREATE_REPORTS',
        }

    project_name = projects_ids_to_names[sys.argv[1]]
    task = tasks[sys.argv[2]]
    operating_system = sys.argv[3]

    print(project_name)
    print(task)

    audio_auditor = AudioAuditor(project_name, operating_system)

    if task == 'CREATE_TRANSCRIPTION_TASKS':
        audio_auditor.create_all_surveys_transcript_tasks()
    elif task == 'LAUNCH_TRANSCRIPT_TASKS':
        audio_auditor.launch_transcript_tasks()
    elif task == 'RECEIVE_AZURE_BATCH_TRANSCRIPTIONS':
        audio_auditor.receive_azure_batch_transcriptions()
    elif task == 'ANALYZE_TRANSCRIPTS':
        audio_auditor.analyze_all_survey_transcripts()
    elif task == 'CREATE_REPORTS':
        report_generation.generate_reports(project_params = audio_auditor.params)
