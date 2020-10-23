cons_1_original_text = '¡Buenos días/tardes/noches! Espero se encuentre bien. Mi nombre es y trabajo para IPA, una organización sin ánimo de lucro que investiga temas relacionados con desarrollo socioeconómico. Nos estamos comunicando con usted porque estamos haciendo una encuesta que no durará más de 20 minutos para conocer como el Coronavirus ha afectado a la población Colombiana. Por su participación recibirá 5,000 pesos de recarga a su celular. ¿Le gustaría participar? '

cons_2_original_text = "Su número fue seleccionado al azar de una lista de números activos en el país.  Utilizaremos sus respuestas para informar al X sobre la mejor manera de proteger a los colombianos. Sus respuestas van a ser totalmente confidenciales y solo se usarán para realizar análisis de la situación actual. Si no desea responder alguna pregunta, puede negarse a responder o detener la encuesta en cualquier momento. Le recuerdo que la llamada será grabada con fines de calidad. Si tiene alguna pregunta o inquietud me la puede hacer en cualquier momento o si prefiere comunicarse con IPA directamente puede hacerlo llamando al número 3218669508 y hablar con Viviana Delgadillo. Igualmente, podrá enviar cualquier comentario a la siguiente dirección en Bogotá: Cl. 98  22-64 oficina 307. ¿Está de acuerdo con contestar esta encuesta? ¿Está de acuerdo con que la llamada sea grabada?" 




#X=Gobierno/investigadores_académicos

FIRST_CONSENT = 'first_consent'
SECOND_CONSENT = 'second_consent'

def get_original_script(survey_part_to_process):
    if survey_part_to_process == FIRST_CONSENT:
        return cons_1_original_text
    elif survey_part_to_process == SECOND_CONSENT:
        return cons_2_original_text
