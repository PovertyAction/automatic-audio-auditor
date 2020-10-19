import os
import pandas as pd
import numpy as np
import string

import transcript_generator
import text_differences
import questionnaire_texts

from columns_specifications import *

FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'

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

def get_audio_audit_path(row, parth_to_audio_audits_dir, survey_part_to_process):

    if(survey_part_to_process == FIRST_CONSENT):
        #In the case of first consent, the path might be in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH or in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS
        if(not pd.isnull(row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH])):
            path =  row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH]
        else:
            path = row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS]

    elif(survey_part_to_process == SECOND_CONSENT):
        path = row[COL_SECOND_CONSENT_AUDIO_AUDIT_PATH]

    #Return False if path is empty
    if path=='':
        return False

    #Path at the moment has format:
    #media\\AA_001df0ef-acdb-4228-8686-9137d8ae0e27-audio_audit_cons_c_call_phone.m4a'
    #Remove media\\ and add directory
    path_cleaned = path.split('\\')[1]

    full_path = os.path.join(parth_to_audio_audits_dir, path_cleaned)

    return full_path

def get_yes_keywords(full_language):
    language = full_language.split('-')[0]
    if language == 'es':
        return ['si','sí','bueno','ok']
    elif language == 'en':
        return ['yes', 'ok']
    else:
        return None

def check_if_respondent_acceptance_is_present(transcript, language):
    #Lets check if any of the acceptance 'words' is present in any of the last 10 words of the transcript

    yes_keywords = get_yes_keywords(language)

    #Clean last 10 words
    exclude = set(string.punctuation)
    def clean_word(word):
        no_punctuation = ''.join(ch for ch in word if ch not in exclude)
        lower_case = no_punctuation.lower()
        return lower_case

    last_10_words = [clean_word(s) for s in transcript.split(' ')[-10:]]
    print(f'Last_10_words: {last_10_words}')

    #Check if any of accepted yes_keywords is present in last 10 words
    for yes_keyword in yes_keywords:
        if yes_keyword in last_10_words:
            print('True')
            return True
    print('False')
    return False


def process_audio_audit(survey_part_to_process, survey_data,
                        language, parth_to_audio_audits_dir):

    audio_path = get_audio_audit_path(survey_data, parth_to_audio_audits_dir, survey_part_to_process)
    if(not audio_path):
        # print("No audio_path")
        return False

    print(f'Working on audio_path {audio_path}')

    transcript = transcript_generator.generate_transcript(audio_path, language)
    print(f'Transcript:{transcript}')

    original_text = questionnaire_texts.get_original_script(survey_part_to_process)
    print(f'Original_text:{original_text}')

    # For classic difference metrics
    # difference_measure = text_differences.compute_standard_difference_measures(original_text, transcript)

    custom_difference_measure, words_missing = text_differences.compute_custom_difference_measure(original_text, transcript)

    acceptance_present = check_if_respondent_acceptance_is_present(transcript, language)

    return {'transcript':transcript,
            'original_text':original_text,
            'audio_path':audio_path,
            'custom_difference_measure':custom_difference_measure,
            'words_missing':words_missing,
            'acceptance_present':acceptance_present}
    #, difference_measure['wer'], difference_measure['mer'], difference_measure['wil']

    # #Save results to csv
    # result_df = pd.DataFrame()
    # result_df = result_df.append(results)
    # result_df.columns=['case_id', 'transcript', 'original_text', 'file_path', 'ROWM', 'words_missing']
    # result_df.to_csv(survey_part_to_process+'_results.csv', index=False)
    # print(result_df)


def analyze_audio_recordings(row, language, consents_audio_audits_path):

    #List with results from processing different audio recording,
    #we will later transform it to a .csv
    results=[]

    case_id = row[COL_CASEID]

    #Process first consent
    fc_results = process_audio_audit(
                        survey_part_to_process = FIRST_CONSENT,
                        survey_data = row,
                        language = language,
                        parth_to_audio_audits_dir = consents_audio_audits_path)

    if fc_results:
        results.append([FIRST_CONSENT,
                        fc_results['transcript'],
                        fc_results['original_text'],
                        fc_results['audio_path'],
                        fc_results['custom_difference_measure'],
                        fc_results['words_missing'],
                        fc_results['acceptance_present']])

    #Save results
    if len(results)>0:
        result_df = pd.DataFrame()
        result_df = result_df.append(results)
        result_df.columns=['Survey_part', 'transcript', 'original_text', 'file_path', 'ROWM', 'words_missing', 'acceptance_present']
        result_df.to_csv(case_id+'_results.csv', index=False)
  # #Process second consent
  # process_audio_audit(  survey_part_to_process = SECOND_CONSENT,
  #                       surveys_df = completed_surveys_df,
  #                       language = language,
  #                       parth_to_audio_audits_dir = parth_to_consensts_audio_audits_dir,
  #                       n_rows_to_process = 5)

    # #Second consent
    # completed_surveys_df$cons2
    # completed_surveys_df$audio_audit_cons_2

    # #Consent to record
    # #-> No audio audit for this question?
    # completed_surveys_df$cons2_audio?


def automatic_backcheck(survey_directory, consents_audio_audits_folder,
                      survey_audio_audits_folder, language):
    '''
    Given audio audits and a questionaire, it checks if the questions and consenst were appropiately delivered
    '''

    survey_path = os.path.join(survey_directory, survey_df_name)

    #Load survey data
    surveys_df, label_dict, value_label_dict = import_data(survey_path)

    consents_audio_audits_path = os.path.join(survey_directory, consents_audio_audits_folder)

    #Get survey attempts that where completed
    completed_surveys_df = get_completed_surveys(surveys_df)

    results = []
    n_rows_to_process = 10#surveys_df.shape[0]

    #Analyze each survey
    for index, row in completed_surveys_df.head(n_rows_to_process).iterrows():
        analyze_audio_recordings(row, language, consents_audio_audits_path)


if __name__=='__main__':

  survey_directory = "X:\\Box Sync\\GRDS_Resources\\Data Science\\Test data\\Raw\\RECOVR_RD1_COL\\"
  survey_df_name = "covid_col_may.dta"
  language = 'es-CO'
  consents_audio_audits_folder = "Audio Audits (Consent)"
  survey_audio_audits_folder = "Audio Audits (Consent)"

  automatic_backcheck(survey_directory = survey_directory,
                      consents_audio_audits_folder= consents_audio_audits_folder,
                      survey_audio_audits_folder = survey_audio_audits_folder,
                      language = language)


#FUTURE, TEXT AUDIT AND GET RECORDED CONSENT
# #Text audit
# text_audit_path = row[COL_TEXT_AUDIT]
#
# #First consent
# #first_consent_recorded_response = get_first_consent_recorded_response(row)
