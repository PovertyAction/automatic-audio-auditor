import jiwer
import nltk
from nltk.stem.snowball import SnowballStemmer
import re

sbEng = SnowballStemmer('english')
sbEsp = SnowballStemmer('spanish')

def get_stemmer(full_language):
    language = full_language.split('-')[0]
    if language=='es':
        return sbEsp
    elif language=='en':
        return sbEng
    else:
        return None

def remove_stopwords(text, full_language):
    language = full_language.split('-')[0]

    if(language=='es'):
        stopwords = nltk.corpus.stopwords.words('spanish')
    elif(language=='en'):
        stopwords = nltk.corpus.stopwords.words('english')
    else:
        return None

    text_without_stopwords = [w for w in text if w not in stopwords]
    return text_without_stopwords

def compute_perc_script_missing(orgininal_script, transcript, language):
    '''
    Check how much of orgininal_script is missing in transcript. Clean and remove stopwords
    '''
    cleaning = jiwer.Compose([
        jiwer.SubstituteRegexes({"¡": "", "¿":"", "á": "a", "é": "e", "í": "i", "ó": "o","ú": "u"}),
        jiwer.SubstituteWords({ "tardes": "dias",
                                "noches": "dias",
                                " uno ": " 1 ",
                                " dos ": " 2 ",
                                " tres ": " 3 ",
                                " cuatro ": " 4 ",
                                " cinco ": " 5 ",
                                " seis ": " 6 ",
                                " siete ": " 7 ",
                                " ocho ": " 8 ",
                                " nueve ": " 9 "}),
        jiwer.RemovePunctuation(),
        jiwer.ToLowerCase(),
        jiwer.SentencesToListOfWords(word_delimiter=" "),
        jiwer.RemoveEmptyStrings()
    ])

    #Remove anything between ${variable} from original_script
    orgininal_script_transformed = re.sub(r'\${.*?\}','',orgininal_script)

    #Clean both
    orgininal_script_transformed = cleaning(orgininal_script_transformed)
    transcript_transformed = cleaning(transcript)

    #Remove stopwords from original_script
    orgininal_script_transformed = remove_stopwords(orgininal_script_transformed, language)

    #Lemmatize transcript
    stemmer = get_stemmer(language)
    transcript_transformed_stem = [stemmer.stem(word) for word in transcript_transformed]

    #Get words form orgininal_script_transformed whose stem is not in transcript_transformed_stem
    words_missing = [word for word in orgininal_script_transformed if stemmer.stem(word) not in transcript_transformed_stem]

    return len(words_missing)/len(orgininal_script_transformed), words_missing

# def compute_standard_difference_measures(ground_truth, transcript, preprocessing=True):
#
#     #Define text preprocessing before comparison
#     transformation = jiwer.Compose([
#         jiwer.RemovePunctuation(),
#         jiwer.ToLowerCase(),
#         # jiwer.Strip(),
#         # jiwer.RemoveMultipleSpaces(),
#         # jiwer.RemoveWhiteSpace(replace_by_space=False),
#         jiwer.SentencesToListOfWords(word_delimiter=" "),
#         # jiwer.Strip(),
#         jiwer.RemoveEmptyStrings(),
#
#         # jiwer.SubstituteWords(dictionary: Mapping[str, str])
#     ])
#         # https://pypi.org/project/jiwer/
#         # default_transformation = jiwer.Compose([
#         #     jiwer.RemoveMultipleSpaces(),
#         #     jiwer.Strip(),
#         #     jiwer.SentencesToListOfWords(),
#         #     jiwer.RemoveEmptyStrings()
#
#     if(preprocessing):
#         measures = jiwer.compute_measures(
#             ground_truth,
#             transcript,
#             truth_transform=transformation,
#             hypothesis_transform=transformation)
#     else:
#         measures = jiwer.compute_measures(
#             ground_truth,
#             transcript)
#
#     return measures#['wer']#, measures['mer'], measures['wil']

if __name__ == '__main__':
    ground_truth = 'mi nombre es felipe alamos illanes'
    hypothesis = 'es felipe alamos illanes'

    print(compute_difference_measures(ground_truth, hypothesis))

    print(compute_difference_measures(ground_truth, hypothesis, preprocessing=True))
