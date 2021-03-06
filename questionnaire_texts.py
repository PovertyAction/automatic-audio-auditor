import pandas as pd
import re

cons_1_original_text = '¡Buenos días! Espero se encuentre bien. Mi nombre es y trabajo para IPA, una organización sin ánimo de lucro que investiga temas relacionados con desarrollo socioeconómico. Nos estamos comunicando con usted porque estamos haciendo una encuesta que no durará más de 20 minutos para conocer como el Coronavirus ha afectado a la población Colombiana. Por su participación recibirá 5,000 pesos de recarga a su celular. ¿Le gustaría participar? '

cons_2_original_text = "Su número fue seleccionado al azar de una lista de números activos en el país.  Utilizaremos sus respuestas para informar al X sobre la mejor manera de proteger a los colombianos. Sus respuestas van a ser totalmente confidenciales y solo se usarán para realizar análisis de la situación actual. Si no desea responder alguna pregunta, puede negarse a responder o detener la encuesta en cualquier momento. Le recuerdo que la llamada será grabada con fines de calidad. Si tiene alguna pregunta o inquietud me la puede hacer en cualquier momento o si prefiere comunicarse con IPA directamente puede hacerlo llamando al número 3218669508 y hablar con Viviana Delgadillo. Igualmente, podrá enviar cualquier comentario a la siguiente dirección en Bogotá: Cl. 98  22-64 oficina 307. ¿Está de acuerdo con contestar esta encuesta? ¿Está de acuerdo con que la llamada sea grabada?"
#X=Gobierno/investigadores_académicos

FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'

def get_original_script(survey_part_to_process):
    if survey_part_to_process == FIRST_CONSENT:
        return cons_1_original_text
    elif survey_part_to_process == SECOND_CONSENT:
        return cons_2_original_text


def get_question_property_2(question_code, property):
    questions_df = pd.read_csv('questions_scripts.csv')
    script_df = questions_df[questions_df['Code']==question_code][property]
    if script_df.shape[0]>0:
        return script_df.iloc[0]
    else:
        return False



def get_question_property(questionnaire_df, question_code, property):
    script_df = questionnaire_df[questionnaire_df['name']==question_code][property]
    if script_df.shape[0]>0:

        response = script_df.iloc[0]
        #Clean label content
        if 'label' in property:
            #Remove anything between <>
            response = re.sub(r'\<.*?\>','',response)
            #Remove anything between []
            response = re.sub(r'\[.*?\]','',response)

            #Remove jumps of line
            response = re.sub(r'[\r\n]+','',response)

            #Remove anything after 'Encuestador/a'
            response = response.split('Encuestador')[0]

            #Remove anything after 'Nota:'
            response = response.split('Nota:')[0]

            #Remove text in upper case like SECCIÓN 7. RED DE SEGURIDAD SOCIAL\
            #Remove anything between SECC and .
            response = re.sub(r'SEC.*?\.','',response)
            response = re.sub(r'\b[A-Z]+\b', '', response)



        return response
    else:
        return False
