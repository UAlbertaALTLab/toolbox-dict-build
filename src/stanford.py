from nltk.parse.corenlp import CoreNLPServer, CoreNLPParser
import os

os.environ["CLASSPATH"]="../stanford-corenlp-4.5.9"

def do_call(pos, sentences):
    default_properties = {
        "ssplit.eolonly": "true",
        "annotators": "tokenize,ssplit,pos,lemma",
    }

    tagged_call = pos.api_call('\n'.join(sentences), properties=default_properties)
    results = [
                [
                    (token["word"], token["pos"], token["lemma"])
                    for token in tagged_sentence["tokens"]
                ]
                for tagged_sentence in tagged_call["sentences"]
            ]
    return results
# The current nltk implementation only accepts pos tags, but we also want lemmas.
# NOTE: The Stanford NLP parser mentions that repeated calls can get very slow
#       and recommends separating on multilines.  This is the process we follow here.
def tag_sentences (sentences : list[str]) -> list[list[tuple[str,str,str]]]:
    processed_data = []
    with CoreNLPServer() as server:
        pos = CoreNLPParser(server.url)
        processed_data = [ sentence for i in range(0,len(sentences),3000) for sentence in do_call(pos, sentences[i:i+3000])]
    return processed_data