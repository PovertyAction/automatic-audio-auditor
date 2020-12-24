import os
import pandas as pd
import numpy as np
import string
import sys

import transcript_generator
import text_differences
import questionnaire_texts
import aa_params

import time
from num2words import num2words
from text_to_num import alpha2digit

from outputs_writer import save_df_to_excel

#Some string constants used along the code
FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'
FULL_SURVEY = 'full_survey'
TEXT_AUDIT = 'text_audit'


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

class QuestionAnalyzer:
    def __init__(self, ta_row, previous_ta_row, next_ta_row, survey_entrie_analyzer):
        self.ta_row = ta_row
        self.previous_ta_row = previous_ta_row
        self.next_ta_row = next_ta_row
        self.survey_entrie_analyzer = survey_entrie_analyzer


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

    def analyze_survey_question(self, read_appropiately_threshold=0.4, read_appropiately_threshold_short_questions=0.55, question_missing_threshold=0.8):

        #Get question name, code, type
        q_full_name = self.ta_row['Field name']
        self.q_code = q_full_name.split('/')[-1]
        print_if_debugging(f'q_code {self.q_code}')

        self.q_type = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'type')
        print_if_debugging(f'q_type {self.q_type}')


        #Do not check notes nor checkpoints
        if  self.q_type == 'note' or 'checkpoint' in self.q_code:
            print_if_debugging(f'Skipping question type {self.q_type}\n')
            #Tell the transcript_generator to forget previous_transcript
            transcript_generator.previous_transcript_to_none()
            return

        #Get question script
        self.q_script = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'label:spanish')

        if not self.q_script:
            print_if_debugging(f"Didnt find question script for {self.q_code}")
            return False
        if len(self.q_script.replace(" ", ""))==0:
            print_if_debugging(f"No question transcript (usually question contianed only instructions for surveyor) for {self.q_code}")
            return False

        print_if_debugging(f'question_script: {self.q_script}')
        # print(f'len question_script: {len(self.q_script)}')

        self.q_transcript = \
            transcript_generator.generate_transcript(
                project_name = self.survey_entrie_analyzer.audio_auditor.params['project_name'],
                case_id = self.survey_entrie_analyzer.case_id,
                q_code = self.q_code,
                audio_url=self.survey_entrie_analyzer.audio_path,
                language=self.survey_entrie_analyzer.audio_auditor.params['language'],
                ta_row = self.ta_row,
                previous_ta_row=self.previous_ta_row,
                next_ta_row=self.next_ta_row,
                first_q_offset=self.survey_entrie_analyzer.start_recording_ta_offset)

        if not self.q_transcript:
            print_if_debugging(f'Couldnt generate transcript for question {self.q_code}')
            return False

        print_if_debugging(f'transcript: {self.q_transcript}')

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

        # print(f"Output for {response['question']} ready\n")

        return response

class SurveyEntrieAnalyzer:
    def __init__(self, audio_auditor, survey_row):
        self.survey_row = survey_row
        self.audio_auditor = audio_auditor
        self.case_id = self.survey_row[audio_auditor.params['col_case_id']]
        self.audio_path = self.get_media_file_path(file_to_get = FULL_SURVEY)
        self.text_audit_df = self.get_text_audit_df()
        self.enumerator_id = self.survey_row[audio_auditor.params['col_enumerator_id']]

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

    def analyze_audio_recording(self):

        # self.print_survey_info()

        if not self.audio_path_exists():
            return False

        #Lets cut down audios for each questions according to text-audits timeframes

        #Text audit capture segments of the interview that are not recorded, particularly the first ones that has surveycto metadata
        #We need to learn when does the recording start, and ends, relative to the beggining of the text audit
        start_recording_ta_index, self.start_recording_ta_offset = self.get_when_recording_starts()
        last_question_index = self.get_last_question_index()

        #Now we analyze each question, looping over the text audit entries
        q_results = []
        previous_ta_row = None
        next_ta_row = None
        for index, ta_row in self.text_audit_df.iterrows():

            #Skip initial part of text audit which are not related to questions
            if(index<start_recording_ta_index or index > last_question_index):
                continue

            next_ta_row = self.text_audit_df.iloc[index+1]

            q_analyzer = QuestionAnalyzer(ta_row, previous_ta_row, next_ta_row, self)

            q_analysis_result = q_analyzer.analyze_survey_question()
            if q_analysis_result:
                q_results.append(q_analysis_result)

            #Keep record of last row
            previous_ta_row = ta_row

        #Save sorted results in a .xlsx
        if len(q_results)>0:
            results_df = pd.DataFrame()
            results_df = results_df.append(q_results, ignore_index=True)



            #Change columns names
            results_df.columns = ['Enum ID', 'Case ID', 'Question code', 'Time Q appears in audio', 'Question missing?', 'Question read inappropiately?', 'Perc. of Q script missing', 'Q words missing', 'Q script', 'Q transcript', 'Congruity between respondents answer and surveyCTO', 'Reason for (in)congruity', 'surveyCTO answer', 'Audio file path', 'Text audit file path']

            #Define columns that should be wide or narrow when saving df to xlsx
            short_entries_cols_index = [0,1,4,5,6,10,12]
            medium_entries_cols_index = [2,3,7,11]
            long_entries_cols_index = [8,9,13,14]

            save_df_to_excel('Caseid_reports/'+self.case_id+'_results.xlsx', results_df,
                short_entries_cols_index=short_entries_cols_index,
                medium_entries_cols_index=medium_entries_cols_index,
                long_entries_cols_index=long_entries_cols_index,
                sort_descending_by = 'Perc. of Q script missing')

        print("")

class AudioAuditor:
    def __init__(self, name):
        self.params = aa_params.get_project_params(name)

    def get_completed_surveys(self, surveys_df):

        #Filter to get only completed surveys
        completed_surveys_df = surveys_df[surveys_df[self.params['col_survey_status']]==self.params['string_completed_survey']]

        #Filter to get surveys with submissiondates after launch day
        if self.params['project_name'] == 'RECOVER_RD3_COL':
            completed_surveys_df = completed_surveys_df[completed_surveys_df['versionform']>='2011172035']

        #Rest index of new df
        completed_surveys_df.reset_index(drop=True, inplace=True)

        return completed_surveys_df

    def filter_completed_surveys_to_only_selected_cases(self):

        #If no specific list of cases for analysis was given, do nothing, we will analyze all of them
        if 'cases_to_check' not in self.params:
            return
        else:
            #Filter according to case id
            selected_cases_ids = self.params['cases_to_check']
            self.completed_surveys_df = self.completed_surveys_df[self.completed_surveys_df[self.params['col_case_id']].isin(selected_cases_ids)]

    def run_audio_audit(self):
        '''
        Given audio audits and a questionaire, it checks if the questions and
        consenst were appropiately delivered, and if answers were appropiately
        recorded
        '''
        #Load survey data
        surveys_df, self.survey_label_dict, self.survey_value_label_dict = import_data(self.params['survey_df_path'])

        #Loas questionnaire
        self.questionnaire_df = pd.read_excel(self.params['questionnaire_path'])

        #Get survey attempts that where completed
        self.completed_surveys_df = self.get_completed_surveys(surveys_df)

        #Filter completed_surveys_df to leave only cases id that were selected for analysis (if no selection made, all will be analyzed)
        self.filter_completed_surveys_to_only_selected_cases()

        n_rows_to_process = self.completed_surveys_df.shape[0]

        print(f'n_rows_to_process {n_rows_to_process}')

        #Analyze each survey
        for index, survey_row in self.completed_surveys_df.head(n_rows_to_process).iterrows():

            survey_response_analyzer = SurveyEntrieAnalyzer(self, survey_row)
            survey_response_analyzer.analyze_audio_recording()


if __name__=='__main__':

    projects_ids_to_names = {'1':'RECOVER_RD1_COL','3':'RECOVER_RD3_COL'}

    project_name = projects_ids_to_names[sys.argv[1]]
    print(project_name)

    audio_auditor = AudioAuditor(project_name)

    audio_auditor.run_audio_audit()


'''
# Deprecated code.

## Used in RD1 RECOVR COL to analyze consents. Should not be needed in other project.

def process_consent_audio_audit(survey_part_to_process, survey_data, language, path_to_audio_audits_dir, read_appropiately_threshold=0.3):

    audio_path = get_media_file_path(survey_data, path_to_audio_audits_dir,
    survey_part_to_process)

    if(not audio_path):
        print_if_debugging("No audio_path")
        return False

    #Check audio exists
    if not os.path.exists(audio_path):
        print_if_debugging(f"Audio {audio_path} does not exist")
        return False

    transcript_sentences = transcript_generator.generate_transcript(audio_path, language)

    question_script = questionnaire_texts.get_original_script(survey_part_to_process)
    # print(f'Original_text:{original_text}')

    full_transcript = " ".join(transcript_sentences)
    perc_script_missing, words_missing = text_differences.compute_perc_script_missing(question_script, full_transcript, language)

    #Check if participation consent question is present in last 3 phrases of transcript
    # participation_concent_question_present = check_if_participation_consent_question_is_present(" ".join(transcript_sentences[-3:]), language)

    #Check if consent yes response is present in last 2 phrases of transcript
    acceptance_present = \
        check_if_respondent_acceptance_is_present(" ".join(transcript_sentences[-2:]),
                                                    language)

    return_dict = {}
    return_dict['question'] = survey_part_to_process
    return_dict['read_appropiately'] = perc_script_missing<read_appropiately_threshold

    # return_dict['participation_concent_question_present'] = participation_concent_question_present
    return_dict['recording_concent_question_present'] = True #Default true given that first consent does not have recording q
    return_dict['acceptance_present'] = acceptance_present

    if return_dict['read_appropiately'] is False:
        return_dict['perc_script_missing'] = perc_script_missing
        return_dict['q_words_missing'] = words_missing
        return_dict['q_and_ans_transcript'] = transcript_sentences
        return_dict['q_script'] = question_script
    else:
        for key in ['perc_script_missing', 'q_words_missing', 'q_and_ans_transcript', 'q_script']:
             return_dict[key]=""


    if survey_part_to_process == SECOND_CONSENT:
        #Check if recording consent question is present in last 3 phrases of transcript
        recording_concent_question_present = check_if_recording_consent_question_is_present(" ".join(transcript_sentences[-3:]), language)
        return_dict['recording_concent_question_present']=recording_concent_question_present

    return return_dict


def check_if_respondent_acceptance_is_present(transcript, language):
    yes_keywords = get_yes_keywords(language)
    return check_if_keywords_are_present(transcript, yes_keywords)

def check_if_participation_consent_question_is_present(transcript, language):
    consent_keywords = ['participar', 'contestar']
    return check_if_keywords_are_present(transcript, consent_keywords)

def check_if_recording_consent_question_is_present(transcript, language):
    recording_keywords = ['grabar', 'grabemos', 'grabe', 'grabada']
    return check_if_keywords_are_present(transcript, recording_keywords)

def check_if_keywords_are_present(transcript, keywords, amount_of_words_to_check = 20):
    #Check if any of keywords is present in any of the last x words of the transcript
    #x depending what part of survey are we checking
    #Clean last x words
    exclude = set(string.punctuation)
    def clean_word(word):
        no_punctuation = ''.join(ch for ch in word if ch not in exclude)
        lower_case = no_punctuation.lower()
        return lower_case

    last_x_words = " ".join([clean_word(s) for s in transcript.split(' ')[-amount_of_words_to_check:]])

    #Check if any keyword is present in last 10 words
    for keyword in keywords:
        if keyword in last_x_words:
            return True
    return False
'''
