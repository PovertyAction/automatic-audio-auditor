import os
import pandas as pd
import numpy as np

import transcript_generator
import text_differences
import questionnaire_texts

from columns_specifications import *

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


def get_first_consent_audio_audit_path(row, directory_path, audio_audits_folder):
  #Path might be in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH or in COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS

  if(not pd.isnull(row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH])):
    path =  row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH]
  else:
    path = row[COL_FIRST_CONSENT_AUDIO_AUDIT_PATH_SMS]

  #Return False if path is empty
  if path=='':
    return False

  #Path at the moment has format:
  #media\\AA_001df0ef-acdb-4228-8686-9137d8ae0e27-audio_audit_cons_c_call_phone.m4a'

  #Remove media\\ and add directory
  path_cleaned = path.split('\\')[1]

  audio_audits_directory_path = os.path.join(directory_path, audio_audits_folder)
  full_path = os.path.join(audio_audits_directory_path, path_cleaned)

  return full_path

def get_first_consent_recorded_response(row):

  #Response might be in COL_FIRST_CONSENT_RESP or in COL_FIRST_CONSENT_SMS_RESP
  #Check which is not null
  if(not pd.isnull(row[COL_FIRST_CONSENT_RESP])):
    return row[COL_FIRST_CONSENT_RESP]
  else:
    return row[COL_FIRST_CONSENT_RESP_SMS]

def automatic_backcheck(survey_directory, consents_audio_audits_folder, survey_df_name, language):
  '''
  Given audio audits and a questionaire, it checks if the questions and consenst were appropiately delivered
  '''
  survey_path = os.path.join(survey_directory, survey_df_name)

  #Load survey data
  surveys_df, label_dict, value_label_dict = import_data(survey_path)

  #Get survey attempts that where completed
  completed_surveys_df = get_completed_surveys(surveys_df)

  #Save results in a df
  results_df = pd.DataFrame(columns=['case_id', 'transcript', 'file_path', 'WER', 'MER', 'WIL','ROWM', 'words_missing'])


  n_rows_to_process = 20#completed_surveys_df.shape[0] #If you want to choose all rows
  #For each completed survye, get its text audit and audio audit.
  for index, row in completed_surveys_df.head(n_rows_to_process).iterrows():

    print(f'{index}/{completed_surveys_df.head(n_rows_to_process).shape[0]}')
    #Case id
    case_id = row[COL_CASEID]

    #Text audit
    text_audit_path = row[COL_TEXT_AUDIT]

    #First consent
    first_consent_recorded_response = get_first_consent_recorded_response(row)

    first_consent_audio_audit_path = get_first_consent_audio_audit_path(row, survey_directory, consents_audio_audits_folder)

    if(first_consent_audio_audit_path):
        print(f'Working on caseid {case_id}')
        transcript = transcript_generator.generate_transcript(first_consent_audio_audit_path, language, adjust_for_ambient_noise=True)

        original_text = questionnaire_texts.cons_original_text

        difference_measure = text_differences.compute_standard_difference_measures(original_text, transcript)

        custom_difference_measure, words_missing = text_differences.compute_custom_difference_measure(original_text, transcript)

        print([case_id, transcript, first_consent_audio_audit_path, difference_measure['wer'], difference_measure['mer'], difference_measure['wil'], custom_difference_measure, words_missing])

        results_df.loc[index] = [case_id, transcript, first_consent_audio_audit_path, difference_measure['wer'], difference_measure['mer'], difference_measure['wil'], custom_difference_measure, words_missing]


  print(results_df)
  results_df.to_csv('results.csv',encoding='utf-8-sig')
    #PENDING:
    # #Second consent
    # completed_surveys_df$cons2
    # completed_surveys_df$audio_audit_cons_2

    # #Consent to record
    # #-> No audio audit for this question?
    # completed_surveys_df$cons2_audio



if __name__=='__main__':

  survey_directory = "X:\\Box Sync\\GRDS_Resources\\Data Science\\Test data\\Raw\\RECOVR_RD1_COL\\"
  survey_df_name = "covid_col_may.dta"
  language = 'es-CO'
  consents_audio_audits_folder = "Audio Audits (Consent)"

  automatic_backcheck(survey_directory, consents_audio_audits_folder, survey_df_name, language)
