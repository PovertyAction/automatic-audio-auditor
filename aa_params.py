projects_params = {
    'RECOVER_RD1_COL': {
        'project_name':'RECOVER_RD1_COL',
        'language' : 'es-CO',
        'survey_df_path' : 'X:\Box\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\covid_col_may.dta',
        'questionnaire_path' : 'X:\Box\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\Questionnaire\covid_col_may_19_5_2020.xlsx',
        'media_folder_path' : "X:\Box\GRDS_Resources\Data Science\Test data\Raw\RECOVR_RD1_COL\media",


        'col_text_audit_path' : 'text_audit_field',

        'q_when_recording_starts' : 'cons1_grp[1]/consented_grp[1]/note_dem',
        'last_question' : 'cons1_grp[1]/consented_grp[1]/note_end_1',
        'survey_cto_yes_no_values': {'yes':'Yes', 'no':'No'},
        'col_enumerator_id': 'enumerator'

        },
    'RECOVER_RD3_COL': {
        'project_name':'RECOVER_RD3_COL',
        'language' : 'es-CO',
        'linux_survey_df_path' : "/mnt/x/Box/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/Encuesta COVID R3.dta",
        'linux_questionnaire_path' : "/mnt/x/Box/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/01 Instruments/03 Final instrument/02 SurveyCTO/202011181- Covid Round 3_IPACOL_3.xlsx",
        'linux_media_folder_path' : "/mnt/x/Box/CP_Projects/IPA_COL_Projects/3_Ongoing Projects/IPA_COL_COVID-19_Survey/07_Questionnaires & Data/04 November/06 rawdata/SurveyCTO/media",
        'windows_survey_df_path' : "X:\\Box\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\Encuesta COVID R3.dta",
        'windows_questionnaire_path' : "X:\\Box\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\01 Instruments\\03 Final instrument\\02 SurveyCTO\\202011181- Covid Round 3_IPACOL_3.xlsx",
        'windows_media_folder_path' : "X:\\Box\\CP_Projects\\IPA_COL_Projects\\3_Ongoing Projects\\IPA_COL_COVID-19_Survey\\07_Questionnaires & Data\\04 November\\06 rawdata\\SurveyCTO\\media",
        'col_text_audit_path' : 'text_audit',

        'q_when_recording_starts' : 'cons2_audio',
        'last_question' : 'consented_grp[1]/END[1]/final_note',
        'col_enumerator_id': 'enum_id',
        'cases_to_check':['1292','1043','11471','16265','11279','17797','10711','11129','10803','10974','11445','11294','11112','13042','12938','11247','13141','11446','12543','11745','12005','11882','11460','16092','12653','12523','10524','17733','11351','13753','21968','11984','1823','9918','10459','20085','16366','13618','7866','14582','11134','11198','14223','11772','1459','14614','12451','15433','15736','11473','15507','1142','16406','10778','138','17492','10232','17418','28444','14102','11852','15791','19125','14003','10572','11583','8212','10717','12107','9950','10909','30116','10810','16062','13639','21427','16566','19224','16832','13080','18511','17952','216','14675','16661','41841','10910','11925','14367','13721','12267','707','14020','10825','14085','11459','14232','1830','26984','12288','19175','19524','10136','19247','18618','12947','20193','11518','15022','20529','17025','16382','16785','15112','20667','22074','27370','25948','8253','10735','12122','17409','10689','14419','19391','20025','15559','14581','15394','16141','15143','11932','19376','15170','20133','16422','21107','17356','12078','16648','19969','14812','20169','19147','31365','11617','12227','1282','10014','2483','10111','15320','10459','11338','15486','11821','19496','11460','22602','13480','12177','13364','14843','24807','14397','15425','12793','31810','18676','24622','10712','5495','10823','12815','11618','10247','14600','12257','10611','14744','12858','12433','13831','12868','20981','12827','21015','13290','15675','31747','18570','10229','18809','27278']
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

def add_agnostic_file_paths(project_name, oprating_system):
    #We will copy info in windoes_file_path or linux_file_path to agnostic file paths
    for key in ['survey_df_path', 'questionnaire_path', 'media_folder_path']:
        projects_params[project_name][key] = projects_params[project_name][oprating_system+'_'+key]


def get_project_params(project_name, oprating_system):
    #Add All projects params
    projects_params[project_name].update(projects_params['ALL_PROJECTS'])

    add_agnostic_file_paths(project_name, oprating_system)

    return projects_params[project_name]
