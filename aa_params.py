projects_params = {
    'RECOVER_RD1_COL': {
        'project_name':'RECOVER_RD1_COL',
        'language' : 'es-CO',
        'survey_df_path' : 'X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\covid_col_may.dta',
        'questionnaire_path' : 'X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\Questionnaire\covid_col_may_19_5_2020.xlsx',
        'media_folder_path' : "X:\Box Sync\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\media",


        'col_text_audit_path' : 'text_audit_field',

        'q_when_recording_starts' : 'cons1_grp[1]/consented_grp[1]/note_dem',
        'last_question' : 'cons1_grp[1]/consented_grp[1]/note_end_1',
        'survey_cto_yes_no_values': {'yes':'Yes', 'no':'No'},
        'col_enumerator_id': 'enumerator'

        },
    'RECOVER_RD3_COL': {
        'project_name':'RECOVER_RD3_COL',
        'language' : 'es-CO',
        'survey_df_path' : "X:\\Box Sync\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\Encuesta COVID R3.dta",
        'questionnaire_path' : "X:\\Box Sync\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\01 Instruments\\03 Final instrument\\02 SurveyCTO\\20201118- Covid Round 3_IPACOL_3.xlsx",
        'media_folder_path' : "X:\\Box Sync\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\media",

        'col_text_audit_path' : 'text_audit',

        'q_when_recording_starts' : 'cons2_audio',
        'last_question' : 'consented_grp[1]/END[1]/final_note',
        'col_enumerator_id': 'enum_id'
        },

    'ALL_PROJECTS' : {
        'string_completed_survey' : 1,
        'survey_cto_yes_no_values': {'yes':[1.0], 'no':[0.0, 2.0]},
        'col_survey_status':'phone_response_answ',
        'col_full_survey_audio_audit_path':'audio_audit_survey',
        'yes_no_question_types': ['select_one yesno','select_one yesno_refusal', 'select_one yesno_dk_refusal', 'select_one yesnodkr'],
        'col_case_id': 'caseid'
    }
}

answers_to_check = []

def get_project_params(project_name):
    #Add All projects params
    projects_params[project_name].update(projects_params['ALL_PROJECTS'])

    return projects_params[project_name]
