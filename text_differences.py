import jiwer

def compute_custom_difference_measure(ground_truth, transcript):
    '''
    Check how much of ground_truth is missing in transcript
    '''
    transformation = jiwer.Compose([
        jiwer.SubstituteRegexes({"¡": "", "¿":""}),
        jiwer.SubstituteWords({"días/tardes/noches": ""}),
        jiwer.RemovePunctuation(),
        jiwer.ToLowerCase(),
        jiwer.SentencesToListOfWords(word_delimiter=" "),
        jiwer.RemoveEmptyStrings()
    ])

    ground_truth_transformed = transformation(ground_truth)
    transcript_transformed = transformation(transcript)

    words_missing = [word for word in ground_truth_transformed if word not in transcript_transformed]

    return len(words_missing)/len(ground_truth_transformed), words_missing

def compute_standard_difference_measures(ground_truth, transcript, preprocessing=True):

    #Define text preprocessing before comparison
    transformation = jiwer.Compose([
        jiwer.RemovePunctuation(),
        jiwer.ToLowerCase(),
        # jiwer.Strip(),
        # jiwer.RemoveMultipleSpaces(),
        # jiwer.RemoveWhiteSpace(replace_by_space=False),
        jiwer.SentencesToListOfWords(word_delimiter=" "),
        # jiwer.Strip(),
        jiwer.RemoveEmptyStrings(),

        # jiwer.SubstituteWords(dictionary: Mapping[str, str])
    ])
        # https://pypi.org/project/jiwer/
        # default_transformation = jiwer.Compose([
        #     jiwer.RemoveMultipleSpaces(),
        #     jiwer.Strip(),
        #     jiwer.SentencesToListOfWords(),
        #     jiwer.RemoveEmptyStrings()

    if(preprocessing):
        measures = jiwer.compute_measures(
            ground_truth,
            transcript,
            truth_transform=transformation,
            hypothesis_transform=transformation)
    else:
        measures = jiwer.compute_measures(
            ground_truth,
            transcript)

    return measures#['wer']#, measures['mer'], measures['wil']

if __name__ == '__main__':
    ground_truth = 'mi nombre es felipe alamos illanes'
    hypothesis = 'es felipe alamos illanes'

    print(compute_difference_measures(ground_truth, hypothesis))

    print(compute_difference_measures(ground_truth, hypothesis, preprocessing=True))
