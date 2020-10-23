import os
import pandas as pd
import numpy as np
import string

import transcript_generator
import text_differences
import questionnaire_texts

from columns_specifications import *

import nltk

FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'
FULL_SURVEY = 'full_survey'

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

    elif(survey_part_to_process == FULL_SURVEY):
        path = row[COL_FULL_SURVEY_AUDIO_AUDIT_PATH]


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

def remove_stopwords(text, full_language):
    language = full_language.split('-')[0]

    if(language=='es'):
        stopwords = nltk.corpus.stopwords.words('spanish')
    elif(language=='en'):
        stopwords = nltk.corpus.stopwords.words('english')
    else:
        return None

    text_without_stopwords =' '.join([w for w in text.split(' ') if w not in stopwords])
    return text_without_stopwords


def process_survey_audio_audit(survey_part_to_process, survey_data,
                        language, parth_to_audio_audits_dir):
    audio_path = get_audio_audit_path(survey_data, parth_to_audio_audits_dir, survey_part_to_process)
    if(not audio_path):
        print("No audio_path")
        return False

    print(f'Working on audio_path {audio_path}')

    transcript = transcript_generator.generate_transcript(audio_path, language)
    print(f'Transcript:{transcript}')


def process_consent_audio_audit(survey_part_to_process, survey_data,
                        language, parth_to_audio_audits_dir):

    audio_path = get_audio_audit_path(survey_data, parth_to_audio_audits_dir, survey_part_to_process)
    if(not audio_path):
        # print("No audio_path")
        return False

    # print(f'Working on audio_path {audio_path}')

    transcript_sentences = transcript_generator.generate_transcript(audio_path, language)#['hola','este es un transcript falso', 'aca','otra cosa']#
    # print(f'Transcript:{transcript_sentences}')

    original_text = questionnaire_texts.get_original_script(survey_part_to_process)
    # print(f'Original_text:{original_text}')

    #Remove stopwords from original_text for computing difference with transcript
    original_text_without_stopwords = remove_stopwords(original_text, language)
    # print(f'original_text_without_stopwords:{original_text_without_stopwords}')

    # For classic difference metrics
    # difference_measure = text_differences.compute_standard_difference_measures(original_text, transcript)

    full_transcript = " ".join(transcript_sentences)
    custom_difference_measure, words_missing = text_differences.compute_custom_difference_measure(original_text_without_stopwords, full_transcript)

    #Check if participation consent question is present in last 3 phrases of transcript
    participation_concent_question_present = check_if_participation_consent_question_is_present(" ".join(transcript_sentences[-3:]), language)

    #Check if consent yes response is present in last 2 phrases of transcript
    acceptance_present = check_if_respondent_acceptance_is_present(" ".join(transcript_sentences[-2:]), language)

    return_dict = {
            'transcript_sentences': transcript_sentences,
            'original_text':original_text,
            'audio_path':audio_path,
            'custom_difference_measure':custom_difference_measure,
            'words_missing':words_missing,
            'participation_concent_question_present': participation_concent_question_present,
            'recording_concent_question_present': True, #Default true given that first consent does not have recording q
            'acceptance_present': acceptance_present}

    if survey_part_to_process == SECOND_CONSENT:
        #Check if recording consent question is present in last 3 phrases of transcript
        recording_concent_question_present = check_if_recording_consent_question_is_present(" ".join(transcript_sentences[-3:]), language)
        return_dict['recording_concent_question_present']=recording_concent_question_present

    return return_dict



def analyze_audio_recordings(row, language, consents_audio_audits_path,survey_audio_audits_path):

    #List with results from processing different audio recording,
    #we will later transform it to a .csv


    case_id = row[COL_CASEID]

    results = []
    #Process first two consents
    for consent_name in [FIRST_CONSENT, SECOND_CONSENT]:
        consent_results = process_consent_audio_audit(
                        survey_part_to_process = consent_name,
                        survey_data = row,
                        language = language,
                        parth_to_audio_audits_dir = consents_audio_audits_path)

        if consent_results:
            #Add case_id and survey_part to results
            consent_results['case_id']= case_id
            consent_results['Survey_part']= consent_name
            results.append(consent_results)


    #Process full survey
    # process_survey_audio_audit(FULL_SURVEY, row, language, survey_audio_audits_path)






    if len(results)>0:
        #Save results in a .csv
        results_df = pd.DataFrame()
        results_df = results_df.append(results)

        results_df.columns=['case_id','Survey_part', 'transcript_sentences', 'original_text', 'audio_path', 'percentage_words_missing', 'words_missing', 'participation_concent_question_present', 'recording_concent_question_present', 'acceptance_present']

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

def automatic_backcheck(survey_directory, consents_audio_audits_folder,
                      survey_audio_audits_folder, language):
    '''
    Given audio audits and a questionaire, it checks if the questions and consenst were appropiately delivered
    '''

    survey_path = os.path.join(survey_directory, survey_df_name)

    #Load survey data
    surveys_df, label_dict, value_label_dict = import_data(survey_path)

    consents_audio_audits_path = os.path.join(survey_directory, consents_audio_audits_folder)
    survey_audio_audits_path = os.path.join(survey_directory, survey_audio_audits_folder)

    #Get survey attempts that where completed
    completed_surveys_df = get_completed_surveys(surveys_df)

    n_rows_to_process = 20#surveys_df.shape[0]

    report = []

    #Analyze each survey
    for index, row in completed_surveys_df.head(n_rows_to_process).iterrows():
        results = analyze_audio_recordings(row=row,
                                language=language,
                                consents_audio_audits_path=consents_audio_audits_path,
                                survey_audio_audits_path=survey_audio_audits_path)

        #Create report of errors
        add_results_to_report(results, row)




if __name__=='__main__':

  survey_directory = "X:\\Box Sync\\GRDS_Resources\\Data Science\\Test data\\Raw\\RECOVR_RD1_COL\\"
  survey_df_name = "covid_col_may.dta"
  language = 'es-CO'
  consents_audio_audits_folder = "Audio Audits (Consent)"
  survey_audio_audits_folder = "Audio Audits (Survey)"

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
