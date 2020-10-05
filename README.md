#Project description

This project aims to use ML to detect problems in survey data.

The current application consists on generating transcripts of survey consents, and detecting differences between transcripts and scripts of what should have been said according to questionnaire.

# Files in repo

## Core of the code:

* backchecker.py: Main file, loads files, get survey responses that were completed and call other modules to compute results
* transcript_generator.py: Creates transcripts, currently with google API
* text_differences.py: Computes measures of differences between texts

# Other utily files:

* questionnaire_texts.py: Scripts that should have been said during survey
* columns_specifications.py: Names of columns in survey df
