#Loading Language Model
import nltk
nltk.download('punkt')
nltk.download('stopwords')

import spacy
spacy.cli.download("en_core_web_sm")

nlp = spacy.load("en_core_web_sm")