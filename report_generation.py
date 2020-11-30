import pandas as pd
from os import listdir
from os.path import isfile, join
from varname import nameof


def get_concatenated_cases_reports(cases_reports_path):

    reports_paths = [join(cases_reports_path, f) for f in listdir(cases_reports_path) if isfile(join(cases_reports_path, f))]

    reports_dfs_list = []
    for report_path in reports_paths:
        report_df = pd.read_csv(report_path)
        reports_dfs_list.append(report_df)

    #Concatenate all individual df
    all_results = pd.concat(reports_dfs_list)

    return all_results


def get_survey_report(case_id, enum_cases_df):
    print(f'Report for case_id {case_id}')

    case_df = enum_cases_df[enum_cases_df['case_id']==case_id]

    #Questions missing
    n_questions_missing = len(case_df[case_df['question_missing']==True])
    questions_missing = case_df[case_df['question_missing']==True]['question'].tolist()

    #Questions read inappropiately
    n_questions_read_inappropiately = len(case_df[case_df['read_inappropiately']==True])
    questions_read_inappropiately = case_df[case_df['read_inappropiately']==True]['question'].tolist()

    #Number of questions with wrong answer in surveycto
    n_questions_answer_error = len(case_df[case_df['answer_matches_surveycto']==False])
    questions_answer_error = case_df[case_df['answer_matches_surveycto']==False]['question'].tolist()

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
    enum_cases_df = cases_reports_df[cases_reports_df['enum_id']==enum_id]
    surveys_cases_ids = enum_cases_df['case_id'].unique()

    #Number of cases done
    n_of_cases = enum_cases_df['case_id'].nunique()
    print(f'n_of_cases {n_of_cases}: {surveys_cases_ids}\n')

    enum_report = {}
    for case_id in surveys_cases_ids:
        survey_report = get_survey_report(case_id, enum_cases_df)
        # print(survey_report)
        enum_report[case_id] = survey_report

    return enum_report


    # print("Summary:")
    # print(f'total_n_questions_missing {total_n_questions_missing}')
    # print(f'total_n_questions_read_inappropiately {total_n_questions_read_inappropiately}')
    # print(f'total_n_questions_answer_error {total_n_questions_answer_error}')
    #
    # return {'enum_id':enum_id,
    #         'n_of_cases':n_of_cases,
    #         'surveys_cases_ids':",".join(surveys_cases_ids),
    #         'total_n_questions_missing':total_n_questions_missing,
    #         'total_n_questions_read_inappropiately':total_n_questions_read_inappropiately,
    #         'total_n_questions_answer_error':total_n_questions_answer_error}


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

        reports_df.to_csv('Main_Report.csv', index=False)
        print(reports_df)

def generate_survey_report(cases_reports_path):

    #Import all casesid reports to one df
    cases_reports_df = get_concatenated_cases_reports(cases_reports_path)

    #Identify all unique surveyors
    enumerators_ids = cases_reports_df['enum_id'].unique()

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
