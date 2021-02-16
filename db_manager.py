import os
import json

def load_database(DB_FILE_NAME):

    #If file does not exist, create it
    # if not os.path.exists(DB_FILE_NAME):
    #     with open(DB_FILE_NAME, "w") as outfile:
    #         # json.dump({}, outfile)
    #         outfile.write('{}')
    #         outfile.close()

    print(f'loading {os.path.abspath(DB_FILE_NAME)}')

    with open(DB_FILE_NAME) as db_file:
        db = json.load(db_file)
        db_file.close()
    return db

def get_element_from_database(database, project_name, case_id, q_code, repeate_group_q = False, repeated_q_number = None):

    #Case its a repeated question
    if repeate_group_q:
        q_code = q_code + '_'+str(repeated_q_number)

    if project_name in database.keys() and \
    case_id in database[project_name] and \
    q_code in database[project_name][case_id]:
        # print_if_debugging(f'Transcript exists for {project_name} {case_id} {q_code}')
        return database[project_name][case_id][q_code]
    else:
        return None


def save_db(database, database_file_name):
    #Save dictionary to json
    #We will use a temporary file copy so as to make it an atomic operation
    #reference: https://stackoverflow.com/questions/2333872/how-to-make-file-creation-an-atomic-operation

    #Create temp_file
    tmp_file = open('tmp_file.json', 'w')
    #Copy data to temp_file
    json.dump(database, tmp_file)
    #Be sure to finish writing all data
    tmp_file.flush()
    os.fsync(tmp_file.fileno())
    #Close file
    tmp_file.close()
    #Rename file
    os.rename('tmp_file.json', database_file_name)

def save_to_db(
    database,
    database_file_name,
    project_name,
    case_id,
    q_code,
    element_to_save,
    repeate_group_q=False,
    repeated_q_number=None):

    #Write to dictionary
    #Creat sub dictionaries if they dont exist
    if project_name not in database:
        database[project_name] = {}
    if case_id not in database[project_name]:
        database[project_name][case_id] = {}

    if repeate_group_q:
        q_code = q_code + '_'+str(repeated_q_number)

    database[project_name][case_id][q_code] = element_to_save

    save_db(database, database_file_name)
