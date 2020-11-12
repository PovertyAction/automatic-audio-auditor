import os
import pandas as pd
import numpy as np
import string

import transcript_generator
import text_differences
import questionnaire_texts

from columns_specifications import *
import time


FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'
FULL_SURVEY = 'full_survey'
TEXT_AUDIT = 'text_audit'

def import_data(dataset_path):
  if dataset_path.endswith('dta'):
    try:
        dataset = pd.read_stata(dataset_path)
    except ValueError:
        dataset = pd.read_stata(dataset_path, convert_categoricals=False)

    label_dict = pd.io.stata.StataReader(dataset_path).variable_labels()
    try:
        value_label_dict = pd.io.stata.StataReader(dataset_path).value_labels()
    except AttributeError:
        status_message = "No value labels detected."
        value_label_dict = None

    return dataset, label_dict, value_label_dict

def get_completed_surveys(surveys_df):
    #Filter based on 'phone_response_answ' column
    completed_surveys_df = surveys_df[surveys_df[COL_SURVEY_STATUS]==COMPLETED_SURVEY_STRING_STATUS]
    #Rest index of new df
    completed_surveys_df.reset_index(drop=True, inplace=True)

    return completed_surveys_df


def get_file_path(row, path_to_file_dir, file_to_get):

    if(file_to_get == FIRST_CONSENT):
        #In the case of first consent, the path might be in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH or in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS
        if(not pd.isnull(row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH])):
            path =  row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH]
        else:
            path = row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS]

    elif(file_to_get == SECOND_CONSENT):
        path = row[COL_SECOND_CONSENT_AUDIO_AUDIT_PATH]

    elif(file_to_get == FULL_SURVEY):
        path = row[COL_FULL_SURVEY_AUDIO_AUDIT_PATH]

    elif(file_to_get == TEXT_AUDIT):
        path = row[COL_TEXT_AUDIT_PATH]

    #Return False if path is empty
    if path=='':
        return False

    #Path at the moment has format:
    #media\\AA_001df0ef-acdb-4228-8686-9137d8ae0e27-audio_audit_cons_c_call_phone.m4a'
    #Remove media\\ and add directory
    path_cleaned = path.split('\\')[1]

    full_path = os.path.join(path_to_file_dir, path_cleaned)

    return full_path

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




def analyze_survey_question(survey_data, audio_path, tex_audit_row, first_q_sec, read_appropiately_threshold=0.25):

    #Get question name, code, appereance and duration
    question_full_name = tex_audit_row['Field name']
    question_code = question_full_name.split('/')[-1]
    q_first_appeared = tex_audit_row['First appeared (seconds into survey)']-first_q_sec
    q_duration = tex_audit_row['Total duration (seconds)']+1

    #Get question script
    question_script = questionnaire_texts.get_question_script(question_code)
    if not question_script:
        print(f"Didnt find question script for {question_code}")
        return False

    #Get transcript for specific question and answer
    q_transcript = transcript_generator.generate_transcript(audio_path, language, offset=q_first_appeared, duration = q_duration)
    if not q_transcript:
        print(f'Couldnt generate transcript for question {question_code}')
        return False

    #Get % of script that was actually pronounced
    full_transcript = " ".join(q_transcript)
    perc_script_missing, words_missing = text_differences.compute_perc_script_missing(question_script, q_transcript, language)

    response = {}

    #Print which question and time are we looking to
    q_first_appeared_formatted = time.strftime('%M:%S', time.gmtime(q_first_appeared))
    q_finished_formatted = time.strftime('%M:%S', time.gmtime(q_first_appeared+q_duration))

    #Compare recorded response with surveycto saved response
    #answer_matches_surveycto = get_surveycto_answer(survey_df, question_code)

    #Prepare response dict
    response['question'] = question_code
    response['time'] = f'{q_first_appeared_formatted}-{q_finished_formatted}'
    response['read_appropiately'] = perc_script_missing<read_appropiately_threshold

    if response['read_appropiately'] is False:
        response['perc_script_missing'] = perc_script_missing
        response['q_words_missing'] = words_missing
        response['q_script'] = question_script
        response['q_and_ans_transcript'] = q_transcript

    response['answer_matches_surveycto'] = 'PENDING' #answer_matches_surveycto

    print(response)

    return response




def process_survey_audio_audit(survey_data, language, audio_audits_dir_path, text_audits_dir_path):

    audio_path = get_file_path(survey_data, audio_audits_dir_path, file_to_get = FULL_SURVEY)

    #Check we have an audio path
    if(not audio_path):
        print("No audio_path")
        return False

    #Check audio exists
    if not os.path.exists(audio_path):
        print(f"Audio {audio_path} does not exist")
        return False

    #Get text audit
    text_audit_path = get_file_path(survey_data, text_audits_dir_path, file_to_get = TEXT_AUDIT)

    # print(f'Working on audio_path {audio_path}')
    # print(f'Text audit {text_audit_path}')

    #Lets cut down audios for each questions, then generate transcripts and compare with question script and answers given.
    text_audit_df = pd.read_csv(text_audit_path)
    first_question = 'cons1_grp[1]/consented_grp[1]/dem2'

    #Get first_question index in df and second of appereance according to text audit
    first_q_df = text_audit_df.loc[text_audit_df['Field name'] == first_question, 'First appeared (seconds into survey)']
    first_question_index = int(first_q_df.index[0])
    first_q_sec = int(first_q_df.iloc[0])

    questions_results = []
    #Now we analyze each question
    for index, row in text_audit_df.head(13).iterrows():

        #Skip initial part of text audit which are not related to questions
        if(index<first_question_index):
            continue

        analysis_result = analyze_survey_question(survey_data, audio_path, row, first_q_sec)
        if analysis_result:
            questions_results.append(analysis_result)

    return questions_results

def process_consent_audio_audit(survey_part_to_process, survey_data,
                        language, path_to_audio_audits_dir, read_appropiately_threshold=0.3):

    audio_path = get_file_path(survey_data, path_to_audio_audits_dir, survey_part_to_process)
    if(not audio_path):
        # print("No audio_path")
        return False

    # print(f'Working on audio_path {audio_path}')

    transcript_sentences = transcript_generator.generate_transcript(audio_path, language)

    question_script = questionnaire_texts.get_original_script(survey_part_to_process)
    # print(f'Original_text:{original_text}')

    # For classic difference metrics
    # difference_measure = text_differences.compute_standard_difference_measures(original_text, transcript)

    full_transcript = " ".join(transcript_sentences)
    perc_script_missing, words_missing = text_differences.compute_perc_script_missing(question_script, full_transcript, language)

    #Check if participation consent question is present in last 3 phrases of transcript
    participation_concent_question_present = check_if_participation_consent_question_is_present(" ".join(transcript_sentences[-3:]), language)

    #Check if consent yes response is present in last 2 phrases of transcript
    acceptance_present = \
        check_if_respondent_acceptance_is_present(" ".join(transcript_sentences[-2:]),
                                                    language)

    return_dict = {}
    return_dict['question'] = survey_part_to_process
    return_dict['read_appropiately'] = perc_script_missing<read_appropiately_threshold

    return_dict['participation_concent_question_present'] = participation_concent_question_present
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



def analyze_audio_recordings(row, language, consents_audio_audits_path, survey_audio_audits_path, text_audits_path):

    #List with results from processing different audio recording,
    #we will later transform it to a .csv
    results = []

    case_id = row[COL_CASEID]
    print(f'Working on case_id {case_id}')


    #Process first two consents
    for consent_name in [FIRST_CONSENT, SECOND_CONSENT]:
        consent_results = process_consent_audio_audit(
                        survey_part_to_process = consent_name,
                        survey_data = row,
                        language = language,
                        path_to_audio_audits_dir = consents_audio_audits_path)

        print(consent_results)
        if consent_results:
            #Add case_id and survey_part to results
            # consent_results['case_id']= case_id
            results.append(consent_results)


    #Process full survey
    audio_audit_result = process_survey_audio_audit(row, language, survey_audio_audits_path, text_audits_path)
    if audio_audit_result:
        results.extend(audio_audit_result)

    if len(results)>0:
        #Save results in a .csv
        results_df = pd.DataFrame(columns=['question', 'read_appropiately', 'perc_script_missing', 'q_words_missing', 'q_and_ans_transcript', 'q_script'])
        results_df = results_df.append(results, ignore_index=True)
        results_df.to_csv(case_id+'_results.csv', index=False)

    return results

def log_and_print(text):
    print(text)

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

def run_audio_audit(survey_directory, consents_audio_audits_folder,
                      survey_audio_audits_folder, text_audits_folder, language):
    '''
    Given audio audits and a questionaire, it checks if the questions and
    consenst were appropiately delivered, and if answers were appropiately
    recorded
    '''

    survey_path = os.path.join(survey_directory, survey_df_name)

    #Load survey data
    surveys_df, label_dict, value_label_dict = import_data(survey_path)

    consents_audio_audits_path = os.path.join(survey_directory, consents_audio_audits_folder)
    survey_audio_audits_path = os.path.join(survey_directory, survey_audio_audits_folder)
    text_audits_path = os.path.join(survey_directory, text_audits_folder)


    #Get survey attempts that where completed
    completed_surveys_df = get_completed_surveys(surveys_df)

    n_rows_to_process = 1#surveys_df.shape[0]

    report = []

    #Analyze each survey
    for index, row in completed_surveys_df.head(n_rows_to_process).iterrows():
        results = analyze_audio_recordings(row=row,
                                language=language,
                                consents_audio_audits_path=consents_audio_audits_path,
                                survey_audio_audits_path=survey_audio_audits_path,
                                text_audits_path=text_audits_path)

        #Create report of errors
        # add_results_to_report(results, row)




if __name__=='__main__':

  survey_directory = "X:\\Box Sync\\GRDS_Resources\\Data Science\\Test data\\Raw\\RECOVR_RD1_COL\\"
  survey_df_name = "covid_col_may.dta"
  language = 'es-CO'
  consents_audio_audits_folder = "Audio Audits (Consent)"
  survey_audio_audits_folder = "Audio Audits (Survey)"
  text_audits_folder = "Text Audits"

  run_audio_audit(survey_directory = survey_directory,
                      consents_audio_audits_folder= consents_audio_audits_folder,
                      survey_audio_audits_folder = survey_audio_audits_folder,
                      text_audits_folder = text_audits_folder,
                      language = language)


#FUTURE, TEXT AUDIT AND GET RECORDED CONSENT
# #Text audit
# text_audit_path = row[COL_TEXT_AUDIT]
#
# #First consent
# #first_consent_recorded_response = get_first_consent_recorded_response(row)
