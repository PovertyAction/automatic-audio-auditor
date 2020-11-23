import os
import pandas as pd
import numpy as np
import string
import sys

import transcript_generator
import text_differences
import questionnaire_texts
import aa_params

from columns_specifications import *
import time
from num2words import num2words
from text_to_num import alpha2digit# as alpha2digit_native

FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'
FULL_SURVEY = 'full_survey'
TEXT_AUDIT = 'text_audit'

# def alpha2digit(word, language)
#     #replace 'una' for 'uno'
#     word = word.replace('Una','Uno')
#     return alpha2digit_native(word, language)

def import_data(dataset_path):
  if dataset_path.endswith('dta'):

      #We might want to do conver_categoricals=True to directly compare transcript answers with surveycto answers
    # try:
    #     dataset = pd.read_stata(dataset_path)
    # except ValueError:
    #     print('EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE')
    dataset = pd.read_stata(dataset_path, convert_categoricals=False)

    label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
    try:
        value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
    except AttributeError:
        status_message = "No value labels detected."
        value_label_dict = None

    return dataset, label_dict, value_label_dict



def get_yes_keywords(full_language):
    language = full_language.split('-')[0]
    if language == 'es':
        return ['si','sí','bueno','ok', 'estoy de acuerdo', 'estoy deacuardo']
    elif language == 'en':
        return ['yes', 'ok']
    else:
        return None

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
    # print(f'Last_x_words: {last_10_words}')

    #Check if any keyword is present in last 10 words
    for keyword in keywords:
        if keyword in last_x_words:
            return True
    return False











def amount_of_words(phrase):
    if phrase:
        return len(phrase.split(' '))
    else:
        return False






class AnswerAnalyzer:
    def __init__(self, q_analyzer):
        self.q_analyzer = q_analyzer

    def analyze_integer_response(self):

        def is_float(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        def is_int(s):
            try:
                int(s)
                return True
            except ValueError:
                return False

        if not is_int(self.surveycto_answer):
            print(f'Surveycto answer not a num: {self.surveycto_answer}')
            return None #or False?

        #Lets look at last phrase in trascript and see if it has the survey_cto_answer
        if str(int(self.surveycto_answer)) in self.q_analyzer.q_transcript[-1] or num2words(self.surveycto_answer, lang='esp') in self.q_analyzer.q_transcript[-1].lower():
            return True

        #Exceptional case for 'ningunx' or 'no'
        elif int(self.surveycto_answer)==0 and \
            ('ningun' in self.q_analyzer.q_transcript[-1].lower() or \
            'no' in [w for w in self.q_analyzer.q_transcript[-1].lower().split(" ")]): #no is a word in the last phrase
            return True

        #Exceptional case for 'background noise
        elif 'background' in self.q_analyzer.q_transcript[-1].lower():
            return None

        #Try to capture number from question_transcript, and check if its != to the one in surveycto
        #Capture numbers
        numeric_values_in_transcript = [int(float(alpha2digit(w,"es"))) \
                                    for w in self.q_analyzer.q_transcript[-1].split(" ") \
                                    if is_float(alpha2digit(w,"es"))]
        #Compare with surveycto answer
        if len(numeric_values_in_transcript)>0:
            if int(self.surveycto_answer)!=numeric_values_in_transcript[-1]:
                return False

        return None

    def check_yes_no_recorded_in_surveycto(self, yes_or_no):
        if self.surveycto_answer in  self.q_analyzer.survey_entrie_analyzer.audio_auditor.params['survey_cto_yes_no_values'][yes_or_no]:
            return True
        else:
            return False

    def analyze_yes_no_response(self):

        def word_exists_in_cleaned_text(text, word):

            def remove_accents(word):
                for a,b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u')]:
                    word = word.replace(a,b)
                return word
            def remove_punctuations(word):
                return word.translate(str.maketrans('', '', string.punctuation))

            clean_text = remove_accents(text)
            clean_text = remove_punctuations(clean_text)
            clean_text = clean_text.lower()

            return word in [w for w in clean_text.split(' ')]

        def get_no_string(language):
            if language=='es':
                return 'no'
            return False

        def get_yes_string(language):
            if language=='es':
                return 'si'
            return False



        #If the question_transcript has too many phrases, it might be the case this questions contains other subquestions all toqueter (fsec3-fsec7 for example), and hence, the text_audit does not separate them, we cant do the analysis
        if len(self.q_analyzer.q_transcript)>6:
            return None

        #We will look for a yes or no in last phrase of transcript
        #Nonetheless, it sometimes happens that last phrase its just a confirmation of the surveyor for the respondents answer.
        #So, what we will do is to concatenate 2 last phrases if they are both short
        last_phrase = self.q_analyzer.q_transcript[-1]

        if len(self.q_analyzer.q_transcript) >1:
            second_last_phrase = self.q_analyzer.q_transcript[-2]
        else:
            second_last_phrase = None

        if amount_of_words(last_phrase) <=2 and amount_of_words(second_last_phrase) <=3:
            phrase_to_analyze = second_last_phrase + " " + last_phrase
        else:
            phrase_to_analyze = last_phrase

        #Correct answer imputed
        #Check a yes was written in survey cto as is found in transcript
        #Check a no was written in survey cto as is found in transcript
        if (self.check_yes_no_recorded_in_surveycto('yes') and \
            word_exists_in_cleaned_text(phrase_to_analyze, get_yes_string(language='es'))) or \
           (self.check_yes_no_recorded_in_surveycto('no') and \
            word_exists_in_cleaned_text(phrase_to_analyze, get_no_string(language='es'))):
            return True

        #Wrong answer imputed
        if (
            self.check_yes_no_recorded_in_surveycto('no') and \
                word_exists_in_cleaned_text(phrase_to_analyze, get_yes_string(language='es'))) or \
           (self.check_yes_no_recorded_in_surveycto('yes') and \
                word_exists_in_cleaned_text(phrase_to_analyze, get_no_string(language='es'))):
            return False

        print('Not being able to recognize answer for YES/NO question')
        return None



    def get_surveycto_answer(self):

        #Check that question code is in survey df
        if self.q_analyzer.q_code in self.q_analyzer.survey_entrie_analyzer.survey_row:
            return self.q_analyzer.survey_entrie_analyzer.survey_row[self.q_analyzer.q_code]
        else:
            return None

    def check_answer_given_matches_surveycto(self):

        #If last phrase of question_transcript is too long (has more than 5 words), then most probably we are missing the answer of respondent (last phrase is from surveyor)
        if len(self.q_analyzer.q_transcript[-1].split(" ")) >5:
            print('Couldnt capture respondets answer')
            return None

        self.surveycto_answer = self.get_surveycto_answer()
        print(f'surveycto_answer {self.surveycto_answer}')
        if self.q_analyzer.q_type == 'integer':
            return self.analyze_integer_response()

        elif self.q_analyzer.q_type in self.q_analyzer.survey_entrie_analyzer.audio_auditor.params['yes_no_question_types']:
            return self.analyze_yes_no_response()


        print(f'Answer analysis for q_type {self.q_analyzer.q_type} of question not implemented')
        # print(question_type)
        # print(question_code)
        # print(question_transcript)
        # print(surveycto_answer)

        return None






def seconds_to_nice_format(time_in_seconds):
    time_nice_format = time.strftime('%M:%S', time.gmtime(time_in_seconds))
    return time_nice_format

class QuestionAnalyzer:
    def __init__(self, ta_row, previous_ta_row, next_ta_row, survey_entrie_analyzer):
        self.ta_row = ta_row
        self.previous_ta_row = previous_ta_row
        self.next_ta_row = next_ta_row
        self.survey_entrie_analyzer = survey_entrie_analyzer

    def analyze_survey_question(self, read_appropiately_threshold=0.5):

        #Get question name, code, type
        q_full_name = self.ta_row['Field name']
        self.q_code = q_full_name.split('/')[-1]
        print(f'q_code {self.q_code}')

        self.q_type = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'type')
        print(f'q_type {self.q_type}')


        #Only checkng integer and yesno for now
        # if  self.q_type != 'integer' and \
        #     self.q_type != 'select_one yesno_dk_refusal' and\
        #     self.q_type != 'select_one yesno_refusal':
        #
        #     print(f'Skipping question type {self.q_type}\n')
        #     #Tell the transcript_generator to forget previous_transcript
        #     transcript_generator.previous_transcript_to_none()
        #     return

        #Get question script
        self.q_script = questionnaire_texts.get_question_property(
            self.survey_entrie_analyzer.audio_auditor.questionnaire_df,
            self.q_code,
            'label:spanish')

        if not self.q_script:
            print(f"Didnt find question script for {self.q_code}")
            return False
        if len(self.q_script)==0 or (len(self.q_script)==1 and self.q_script==" "):
            print(f"No question transcript (usually q contianed only instructions for surveyor) for {self.q_code}")
            return False

        # print(f'question_script: {self.q_script}')

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
            print(f'Couldnt generate transcript for question {self.q_code}')
            return False

        print(f'transcript: {self.q_transcript}')

        #Get % of script that was actually pronounced
        full_transcript = " ".join(self.q_transcript)
        perc_script_missing, words_missing = text_differences.compute_perc_script_missing(self.q_script, self.q_transcript, self.survey_entrie_analyzer.audio_auditor.params['language'])

        response = {}

        #Compare recorded response with surveycto saved response
        answer_analyzer = AnswerAnalyzer(self)
        answer_matches_surveycto = answer_analyzer.check_answer_given_matches_surveycto()

        #Getting this again just to inlcude it in response
        q_first_appeared, q_duration = transcript_generator.get_first_appeared_and_duration(
        ta_row=self.ta_row, previous_ta_row=self.previous_ta_row, first_q_offset= self.survey_entrie_analyzer.start_recording_ta_offset)

        #Prepare response dict
        response['question'] = self.q_code
        response['time_in_audio'] = \
            f'{seconds_to_nice_format(q_first_appeared)}-{seconds_to_nice_format(q_first_appeared+q_duration)}'
        response['read_appropiately'] = perc_script_missing<read_appropiately_threshold

        if response['read_appropiately'] is False:
            response['perc_script_missing'] = perc_script_missing
            response['q_words_missing'] = words_missing
            response['q_script'] = self.q_script
            response['q_and_ans_transcript'] = self.q_transcript

        response['answer_matches_surveycto'] = answer_matches_surveycto

        print(f'Output: {response}')
        print("")

        return response




def process_consent_audio_audit(survey_part_to_process, survey_data, language, path_to_audio_audits_dir, read_appropiately_threshold=0.3):

    audio_path = get_media_file_path(survey_data, path_to_audio_audits_dir,
    survey_part_to_process)

    if(not audio_path):
        print("No audio_path")
        return False

    #Check audio exists
    if not os.path.exists(audio_path):
        print(f"Audio {audio_path} does not exist")
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






def add_results_to_report(results, row, words_missing_rate_threshold = 0.3):
    for result in results: #One result for each part of survey
        print_result = False

        #Check that consent was read approximately completely
        if result['custom_difference_measure'] > words_missing_rate_threshold:
            log_and_print(f"Case_id {result['case_id']}, {result['Survey_part']}: {int(result['custom_difference_measure']*100)}% of consent script is missing")
            log_and_print(" ".join(result['transcript_sentences']))
            print_result=True

        #Check that consent questions are present
        if result['participation_concent_question_present'] is False:
            log_and_print(f"Case_id {result['case_id']}, {result['Survey_part']}: Surveyor might have not asked participation consent question")
            log_and_print(" ".join(result['transcript_sentences'][-4:]))
            print_result=True

        if result['recording_concent_question_present'] is False:
            log_and_print(f"Case_id {result['case_id']}, {result['Survey_part']}: Surveyor might have not asked recording consent question")
            log_and_print(" ".join(result['transcript_sentences'][-4:]))
            print_result=True

        #Check acceptance to consent is present
        if result['acceptance_present'] is False:
            log_and_print(f"Case_id {result['case_id']}, {result['Survey_part']}: Respondent acceptance to consent might not be present")
            log_and_print(" ".join(result['transcript_sentences'][-4:]))
            print_result=True

        if print_result:
            print(f"Consent audio path: {result['audio_path']}")
            print(f'Full survey audio path: {row[COL_FULL_SURVEY_AUDIO_AUDIT_PATH]}')
            print("////////////////////////////////////////////")

class SurveyEntrieAnalyzer:
    def __init__(self, audio_auditor, survey_row):
        self.survey_row = survey_row
        self.audio_auditor = audio_auditor

    def get_when_recording_starts(self):
        q_when_recording_starts_df = self.text_audit_df.loc[self.text_audit_df['Field name'] == self.audio_auditor.params['q_when_recording_starts']]
        start_recording_ta_index = int(q_when_recording_starts_df.index[0])
        start_recording_ta_offset = int(q_when_recording_starts_df['First appeared (seconds into survey)'].iloc[0])
        return start_recording_ta_index, start_recording_ta_offset

    def audio_path_exists(self):
        if(not self.audio_path):
            print("No audio_path")
            return False

        #Check audio exists
        if not os.path.exists(self.audio_path):
            print(f"Audio {self.audio_path} does not exist")
            return False

        return True

    def get_text_audit_df(self):
        text_audit_path = self.get_media_file_path(file_to_get = TEXT_AUDIT)
        text_audit_df = pd.read_csv(text_audit_path)
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
        print(f"Case_id {self.survey_row[COL_CASEID]}")
        print(f"Text_audit {self.survey_row[self.audio_auditor.params['col_text_audit_path']]}")#
        # print(f"Firt consent {self.survey_row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH]}")
        # print(f"Second consent {self.survey_row[COL_SECOND_CONSENT_AUDIO_AUDIT_PATH]}")
        print(f"Full survey {self.survey_row[self.audio_auditor.params['col_full_survey_audio_audit_path']]}")

    def analyze_audio_recording(self):

        self.case_id = self.survey_row[COL_CASEID]
        self.print_survey_info()

        self.audio_path = self.get_media_file_path(file_to_get = FULL_SURVEY)
        if not self.audio_path_exists():
            return False

        #Get text audit
        self.text_audit_df = self.get_text_audit_df()

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

        #Save results in a .csv
        if len(q_results)>0:
            results_df = pd.DataFrame(columns=['question', 'time_in_audio','read_appropiately', 'perc_script_missing', 'q_words_missing', 'q_and_ans_transcript', 'q_script'])
            results_df = results_df.append(q_results, ignore_index=True)
            results_df.to_csv(self.case_id+'_results.csv', index=False)

        print("")
        return q_results


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

        n_rows_to_process = self.completed_surveys_df.shape[0]

        # report = []

        #Analyze each survey
        for index, survey_row in self.completed_surveys_df.head(n_rows_to_process).iterrows():

            survey_response_analyzer = SurveyEntrieAnalyzer(self, survey_row)
            results = survey_response_analyzer.analyze_audio_recording()

            #Create report of errors
            # add_results_to_report(results, row)

if __name__=='__main__':

    projects_ids_to_names = {'1':'RECOVER_RD1_COL','3':'RECOVER_RD3_COL'}

    project_name = projects_ids_to_names[sys.argv[1]]
    print(project_name)

    audio_auditor = AudioAuditor(project_name)

    audio_auditor.run_audio_audit()
