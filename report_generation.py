import pandas as pd
from os import listdir
from os.path import isfile, join
from varname import nameof
from outputs_writer import save_df_to_excel

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
    print(f'Report for case_id {case_id}')

    case_df = enum_cases_df[enum_cases_df['Case ID']==case_id]

    #Questions missing
    n_questions_missing = len(case_df[case_df['Question missing?']==True])
    questions_missing = case_df[case_df['Question missing?']==True]['Question code'].tolist()

    #Questions read inappropiately
    n_questions_read_inappropiately = len(case_df[case_df['Question read inappropiately?']==True])
    questions_read_inappropiately = case_df[case_df['Question read inappropiately?']==True]['Question code'].tolist()

    #Number of questions with wrong answer in surveycto
    n_questions_answer_error = len(case_df[case_df['Congruity between respondents answer and surveyCTO']==False])
    questions_answer_error = case_df[case_df['Congruity between respondents answer and surveyCTO']==False]['Question code'].tolist()

    # print(f'n_questions_missing {n_questions_missing}: {questions_missing}')
    # print(f'n_questions_read_inappropiately {n_questions_read_inappropiately}: {questions_read_inappropiately}')
    # print(f'n_questions_answer_error {n_questions_answer_error}: {questions_answer_error}')
    # print("")

    #Add results to dict
    report = {
        'n_questions_missing':n_questions_missing,
        'questions_missing':questions_missing,

        'n_questions_read_inappropiately':n_questions_read_inappropiately,
        'questions_read_inappropiately':questions_read_inappropiately,

        'n_questions_answer_error':n_questions_answer_error,
        'questions_answer_error':questions_answer_error
        }
    # print(report)
    return report

def create_enum_report(enum_id, cases_reports_df):
    print("************************")
    print(f'REPORT FOR ENUM {enum_id}')

    #All cases done by this enumerator
    enum_cases_df = cases_reports_df[cases_reports_df['Enum ID']==enum_id]
    surveys_cases_ids = enum_cases_df['Case ID'].unique()

    #Number of cases done
    n_of_cases = enum_cases_df['Case ID'].nunique()
    print(f'n_of_cases {n_of_cases}: {surveys_cases_ids}\n')

    enum_report = {}
    for case_id in surveys_cases_ids:
        survey_report = get_survey_report(case_id, enum_cases_df)
        # print(survey_report)
        enum_report[case_id] = survey_report

    return enum_report

def save_results_to_csv(survey_report):

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

        save_df_to_excel('Survey_Reportt.xlsx', reports_df,
            short_entries_cols_index=short_entries_cols_index,
            medium_entries_cols_index=medium_entries_cols_index,
            long_entries_cols_index=long_entries_cols_index)

        print(reports_df)

def generate_survey_report(cases_reports_path):

    #Import all casesid reports to one df
    cases_reports_df = get_concatenated_cases_reports(cases_reports_path)

    #Identify all unique surveyors
    enumerators_ids = cases_reports_df['Enum ID'].unique()

    #For each surveyor, filter df and compute stats
    survey_report = {}
    for enum_id in enumerators_ids:
        enum_report = create_enum_report(enum_id, cases_reports_df)
        survey_report[enum_id] = enum_report

    print("survey_report")
    print(survey_report)

    save_results_to_csv(survey_report)


if __name__ == '__main__':

    cases_reports_path = 'Caseid_reports'

    generate_survey_report(cases_reports_path)
