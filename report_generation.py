import pandas as pd
from os import listdir
from os.path import isfile, join
from varname import nameof
import outputs_writer
from name_reports_columns import *

def get_concatenated_cases_reports(cases_reports_path):

    reports_paths = [join(cases_reports_path, f) for f in listdir(cases_reports_path) if isfile(join(cases_reports_path, f))]

    reports_dfs_list = []
    for report_path in reports_paths:
        report_df = pd.read_excel(report_path)
        reports_dfs_list.append(report_df)

    #Concatenate all individual df
    all_results = pd.concat(reports_dfs_list)

    return all_results


def get_survey_report(case_id, enum_cases_df):

    case_df = enum_cases_df[enum_cases_df[col_case_id]==case_id]

    #Questions missing
    n_questions_missing = len(case_df[case_df[col_q_missing]==True])
    questions_missing = case_df[case_df[col_q_missing]==True][col_q_code].tolist()

    #Questions read inappropiately
    n_questions_read_inappropiately = len(case_df[case_df[col_q_read_inappropiately]==True])
    questions_read_inappropiately = case_df[case_df[col_q_read_inappropiately]==True][col_q_code].tolist()

    #Number of questions with wrong answer in surveycto
    n_questions_answer_error = len(case_df[case_df[col_answer_congruity]==False])
    questions_answer_error = case_df[case_df[col_answer_congruity]==False][col_q_code].tolist()

    #Add results to dict
    report = {
        'n_questions_missing':n_questions_missing,
        'questions_missing':questions_missing,

        'n_questions_read_inappropiately':n_questions_read_inappropiately,
        'questions_read_inappropiately':questions_read_inappropiately,

        'n_questions_answer_error':n_questions_answer_error,
        'questions_answer_error':questions_answer_error
        }
    return report

def create_enum_report(enum_id, cases_reports_df):

    #All cases done by this enumerator
    enum_cases_df = cases_reports_df[cases_reports_df[col_enum_id]==enum_id]
    surveys_cases_ids = enum_cases_df[col_case_id].unique()

    #Number of cases done
    n_of_cases = enum_cases_df[col_case_id].nunique()

    enum_report = {}
    for case_id in surveys_cases_ids:
        survey_report = get_survey_report(case_id, enum_cases_df)
        enum_report[case_id] = survey_report

    return enum_report

def create_question_report(question_code, cases_reports_df):

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



def save_question_level_report(q_level_report):

    reports_df = pd.DataFrame(columns=[
                                col_q_code,
                                col_q_missing,
                                col_q_read_inappropiately])

    for i, q_code in enumerate(q_level_report.keys()):
        row = [ q_code,
                q_level_report[q_code]['n_times_question_is_missing'],
                q_level_report[q_code]['n_times_question_read_inappropiately']]

        reports_df.loc[i] = row

    print(reports_df)
    outputs_writer.save_df_to_excel('Question Level Report.xlsx', reports_df, medium_entries_cols_index=[0,1,2], sort_descending_by=col_q_missing)


def save_surveyor_level_report(survey_report):

    def get_metric_sum_across_all_cases(survey_report, enum_id, metric):

        metric_sum = \
            sum([survey_report[enum_id][case_id][metric]
            for case_id in survey_report[enum_id].keys()])
        return metric_sum

    def get_elements_across_all_cases(survey_report, enum_id, element):
        all_elements = {}
        for case_id in survey_report[enum_id]:
            elements = survey_report[enum_id][case_id][element]
            if len(elements)>0:
                all_elements[case_id] = elements

        if len(all_elements)>0:
            return all_elements
        else:
            return ""

    if len(survey_report)>0:
        reports_df = pd.DataFrame(
            columns=['enum_id',
                    'n_of_cases',
                    'cases_ids',
                    'total_n_questions_missing',
                    'all_questions_missing',
                    'total_n_questions_read_inappropiately',
                    'all_questions_read_inappropiately',
                    'total_n_questions_answer_error',
                    'all_questions_answer_error'])

        for enum_id in survey_report.keys():
            n_of_cases = len(survey_report[enum_id])
            cases_ids = list(survey_report[enum_id].keys())

            total_n_questions_missing = \
                get_metric_sum_across_all_cases(survey_report, enum_id, 'n_questions_missing')
            all_questions_missing = \
                get_elements_across_all_cases(survey_report, enum_id, 'questions_missing')

            total_n_questions_read_inappropiately = \
                get_metric_sum_across_all_cases(survey_report, enum_id, 'n_questions_read_inappropiately')
            all_questions_read_inappropiately = \
                get_elements_across_all_cases(survey_report, enum_id, 'questions_read_inappropiately')

            total_n_questions_answer_error = \
                get_metric_sum_across_all_cases(survey_report, enum_id, 'n_questions_answer_error')
            all_questions_answer_error = \
                get_elements_across_all_cases(survey_report, enum_id, 'questions_answer_error')


            enum_report_row = {
                'enum_id':enum_id,
                'n_of_cases':n_of_cases,
                'cases_ids':cases_ids,
                'total_n_questions_missing':total_n_questions_missing,
                'all_questions_missing':all_questions_missing,
                'total_n_questions_read_inappropiately':total_n_questions_read_inappropiately,
                'all_questions_read_inappropiately':all_questions_read_inappropiately,
                'total_n_questions_answer_error':total_n_questions_answer_error,
                'all_questions_answer_error':all_questions_answer_error}

            reports_df = reports_df.append(enum_report_row, ignore_index=True)

        reports_df.columns = ['Enumerator ID', 'N of cases', 'Cases ids', 'Total N of Q missing', 'Q missing by caseid', 'Total N of Q read inappropiately', 'Q  read inappropiately by caseid', 'N of Q with wrong answer', 'Q with wrong answer by caseid']


        short_entries_cols_index = [0,1,3,5,7]
        medium_entries_cols_index = [2]
        long_entries_cols_index = [4,6,8]

        print(reports_df)
        outputs_writer.save_df_to_excel('Surveyor Level Report.xlsx', reports_df,
            short_entries_cols_index=short_entries_cols_index,
            medium_entries_cols_index=medium_entries_cols_index,
            long_entries_cols_index=long_entries_cols_index)


def generate_surveyor_level_report(cases_reports_df):

    #Identify all unique surveyors
    enumerators_ids = cases_reports_df[col_enum_id].unique()

    #For each surveyor, filter df and compute stats
    surveyor_level_report = {}
    for enum_id in enumerators_ids:
        enum_report = create_enum_report(enum_id, cases_reports_df)
        surveyor_level_report[enum_id] = enum_report

    save_surveyor_level_report(surveyor_level_report)


def generate_question_level_report(cases_reports_df):

    #Identify all unique questions
    question_codes = cases_reports_df[col_q_code].unique()

    #For each question, filter df and compute stats
    question_level_report = {}
    for question_code in question_codes:
        question_report = create_question_report(question_code, cases_reports_df)
        question_level_report[question_code] = question_report

    save_question_level_report(question_level_report)

def generate_report(cases_reports_path):
    #Import all casesid reports to one df
    cases_reports_df = get_concatenated_cases_reports(cases_reports_path)

    generate_surveyor_level_report(cases_reports_df)

    generate_question_level_report(cases_reports_df)

if __name__ == '__main__':

    cases_reports_path = 'Caseid_reports'

    generate_report(cases_reports_path)
