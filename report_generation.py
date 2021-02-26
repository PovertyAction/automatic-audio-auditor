import pandas as pd
import os
from os import listdir
from os.path import isfile
import outputs_writer
import sys
from name_reports_columns import *
import aa_params
import db_manager
from file_names import *

def get_concatenated_cases_reports(cases_reports_path, project_params):

    #Create list of cases id file reports
    #Filter to only certain cases ids if cases_to_check param is given
    if 'cases_to_check' in project_params:
        reports_paths = [os.path.join(cases_reports_path, f) \
                        for f in listdir(cases_reports_path) \
                        if isfile(os.path.join(cases_reports_path, f)) and \
                            f.split('_')[0] in project_params['cases_to_check']]
        print('Will generate report for only certain cases ids')
    else:
        reports_paths = [os.path.join(cases_reports_path, f) \
                    for f in listdir(cases_reports_path) \
                    if isfile(os.path.join(cases_reports_path, f))]

    reports_dfs_list = []
    for report_path in reports_paths:
        report_df = pd.read_excel(report_path)
        reports_dfs_list.append(report_df)

    #Concatenate all individual df
    all_results = pd.concat(reports_dfs_list)

    return all_results

def generate_surveyor_level_report(path_to_project_reports, cases_reports_df):

    #Identify all unique surveyors
    enumerators_ids = cases_reports_df[col_enum_id].unique()

    #Create df with results
    reports_df = pd.DataFrame(
        columns=['enum_id',
                'n_of_cases',
                'cases_ids',
                'n_questions_missing',
                'questions_missing',
                'n_questions_read_inappropiately',
                'questions_read_inappropiately',
                'n_questions_answer_error',
                'questions_answer_error'])

    for enum_id in enumerators_ids:

        #All cases done by this enumerator
        enum_cases_df = cases_reports_df[cases_reports_df[col_enum_id]==enum_id]

        #Number of cases done
        n_of_cases = enum_cases_df[col_case_id].nunique()

        #Cases
        cases_ids = enum_cases_df[col_case_id].unique()

        def get_questions_and_counts(enum_cases_df, col_criteria, true_false_criteria):
        #Compute how many times each question matches criteria (missing, read inappropiately, or presents incongruency)
            all_q_codes_that_match_criteria = enum_cases_df[enum_cases_df[col_criteria]==true_false_criteria][col_q_code].tolist()
            q_and_counts = {}
            for q_code in set(all_q_codes_that_match_criteria):
                q_and_counts[q_code] = all_q_codes_that_match_criteria.count(q_code)

            #Return sorted list of tuples
            sorted_tuples_q_and_counts = []
            for q in sorted(q_and_counts, key=q_and_counts.get, reverse=True):
                sorted_tuples_q_and_counts.append((q, q_and_counts[q]))

            return sorted_tuples_q_and_counts

        #N questions missing
        n_questions_missing = len(enum_cases_df[enum_cases_df[col_q_missing]==True])
        questions_missing = get_questions_and_counts(enum_cases_df, col_q_missing, true_false_criteria=True)

        #Questions read inappropiately
        n_questions_read_inappropiately = len(enum_cases_df[enum_cases_df[col_q_read_inappropiately]==True])
        questions_read_inappropiately = get_questions_and_counts(enum_cases_df, col_q_read_inappropiately, true_false_criteria=True)

        #Number of questions with wrong answer in surveycto
        n_questions_answer_error = len(enum_cases_df[enum_cases_df[col_answer_congruity]==False])
        questions_answer_error = get_questions_and_counts(enum_cases_df, col_answer_congruity, true_false_criteria=False)

        enum_report_row = {
            'enum_id':enum_id,
            'n_of_cases':n_of_cases,
            'cases_ids':cases_ids,
            'n_questions_missing':n_questions_missing,
            'questions_missing':questions_missing,
            'n_questions_read_inappropiately':n_questions_read_inappropiately,
            'questions_read_inappropiately':questions_read_inappropiately,
            'n_questions_answer_error':n_questions_answer_error,
            'questions_answer_error':questions_answer_error}

        reports_df = reports_df.append(enum_report_row, ignore_index=True)

    reports_df.columns = ['Enumerator ID', 'N of cases', 'Cases ids', 'N of Q missing', 'Q missing', 'N of Q read inappropiately', 'Q read inappropiately', 'N of Q with wrong answer', 'Q with wrong answer']


    short_entries_cols_index = [0,1,3,5,7]
    medium_entries_cols_index = [2]
    long_entries_cols_index = [4,6,8]


    outputs_writer.save_df_to_excel(
        saving_path = os.path.join(path_to_project_reports, 'Surveyor Level Report.xlsx'),
        df_to_save = reports_df,
        short_entries_cols_index=short_entries_cols_index,
        medium_entries_cols_index=medium_entries_cols_index,
        long_entries_cols_index=long_entries_cols_index)

def generate_question_level_report(path_to_project_reports, cases_reports_df):

    def get_q_stats(question_code, cases_reports_df):

        #Filter data for this question
        question_df = cases_reports_df[cases_reports_df[col_q_code]==question_code]

        #Compute stats
        n_times_question_is_missing = sum(question_df[col_q_missing])
        n_times_question_read_inappropiately= sum(question_df[col_q_read_inappropiately])
        # n_times_answer_error = sum(question_df[col_answer_congruity])

        question_report = {}
        question_report['n_times_question_is_missing'] = n_times_question_is_missing
        question_report['n_times_question_read_inappropiately'] = n_times_question_read_inappropiately

        return question_report

    #Identify all unique questions
    question_codes = cases_reports_df[col_q_code].unique()

    #For each question, filter df and compute stats
    q_level_report = {}
    for question_code in question_codes:
        q_stats = get_q_stats(question_code, cases_reports_df)
        q_level_report[question_code] = q_stats

    reports_df = pd.DataFrame(columns=[
                                col_q_code,
                                col_q_missing,
                                col_q_read_inappropiately])

    for i, q_code in enumerate(q_level_report.keys()):
        row = [ q_code,
                q_level_report[q_code]['n_times_question_is_missing'],
                q_level_report[q_code]['n_times_question_read_inappropiately']]

        reports_df.loc[i] = row

    outputs_writer.save_df_to_excel(
        saving_path = os.path.join(path_to_project_reports, 'Question Level Report.xlsx'),
        df_to_save = reports_df,
        medium_entries_cols_index=[0,1,2],
        sort_descending_by=col_q_missing)

def generate_case_level_reports(path_to_project_reports, project_name):

    #Create cases folder
    path_to_cases_reports = os.path.join(path_to_project_reports, 'Cases Reports')
    if not os.path.exists(path_to_cases_reports):
        os.makedirs(path_to_cases_reports)

    project_question_analysis_db = \
        db_manager.load_database(QUESTION_ANALYSIS_DB_FILE_NAME)[project_name]

    #For each case, create a report
    for case_id in project_question_analysis_db.keys():

        #Transform json to list
        q_results = []

        for q_code in project_question_analysis_db[case_id].keys():
            q_results.append(project_question_analysis_db[case_id][q_code])


        #Save results in a .xlsx
        if len(q_results)>0:
            results_df = pd.DataFrame()
            results_df = results_df.append(q_results, ignore_index=True)

            #Change columns names
            results_df.columns = ['Enum ID', 'Case ID', 'Question code', 'Time Q appears in audio', 'Question missing?', 'Question read inappropiately?', 'Perc. of Q script missing', 'Q words missing', 'Q script', 'Q transcript', 'Congruity between respondents answer and surveyCTO', 'Reason for (in)congruity', 'surveyCTO answer', 'Audio file path', 'Text audit file path']

            #Define columns that should be wide or narrow when saving df to xlsx
            short_entries_cols_index = [0,1,4,5,6,10,12]
            medium_entries_cols_index = [2,3,7,11]
            long_entries_cols_index = [8,9,13,14]

            outputs_writer.save_df_to_excel(
                saving_path = os.path.join(path_to_cases_reports, case_id+'_results.xlsx'),
                df_to_save = results_df,
                short_entries_cols_index=short_entries_cols_index,
                medium_entries_cols_index=medium_entries_cols_index,
                long_entries_cols_index=long_entries_cols_index,
                sort_descending_by = 'Perc. of Q script missing')


def generate_and_save_all_cases_report(path_to_project_reports, project_params):

    cases_reports_df = get_concatenated_cases_reports(os.path.join(path_to_project_reports, 'Cases Reports'), project_params)

    outputs_writer.save_df_to_excel(
        saving_path = os.path.join(path_to_project_reports,'All cases.xlsx'),
        df_to_save = cases_reports_df,
        short_entries_cols_index=[0,1,4,5,6,10,12],
        medium_entries_cols_index=[2,3,7,11],
        long_entries_cols_index=[8,9,13,14],
        sort_descending_by=col_perc_q_missing)

    return cases_reports_df

def generate_reports(project_params):

    #Create folder structure
    path_to_project_reports = os.path.join('Reports', project_params['project_name'])
    if not os.path.exists(path_to_project_reports):
        os.makedirs(path_to_project_reports)

    print('Starting generate_case_level_reports')
    generate_case_level_reports(path_to_project_reports, project_params['project_name'])

    print('Starting generate_and_save_all_cases_report')
    cases_reports_df = generate_and_save_all_cases_report(path_to_project_reports, project_params)

    print('Starting generate_surveyor_level_report')
    generate_surveyor_level_report(path_to_project_reports, cases_reports_df)

    print('Starting generate_question_level_report')
    generate_question_level_report(path_to_project_reports, cases_reports_df)

if __name__ == '__main__':

    projects_ids_to_names = {'1':'RECOVER_RD1_COL','3':'RECOVER_RD3_COL'}
    project_name = projects_ids_to_names[sys.argv[1]]

    operating_system = sys.argv[2]
    print(project_name)

    project_params = aa_params.get_project_params(project_name, operating_system)

    generate_reports(project_params)
