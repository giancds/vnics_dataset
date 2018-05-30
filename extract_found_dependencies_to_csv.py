""" Module to process the corpus and obtain the VNICs dataset. """

import codecs
import json
import os

import pandas as pd
from pycorenlp import StanfordCoreNLP
from dependencies import process_dependencies, process_json

# pylint: disable=C0103

BASE_DIR = os.path.expanduser("~")   # this will point to the user's home
FILE_PATH = os.path.join(BASE_DIR, "data/BNC.txt")
PARTIAL_FILE = os.path.join(BASE_DIR, "data/BNC.counts.{}")

properties = {
  "annotators": "tokenize,ssplit,pos,depparse,lemma",
  "outputFormat": "json"
}

nlp = StanfordCoreNLP('http://localhost:9000')

QUERY_STRING = ("(verb == '{0}') & (verb_POS == '{1}') & (noun == '{2}') & "
                "(noun_POS == '{3}') & (det == '{4}') & (pattern == {5})")

start_at = 0
keep_all_dependencies = False
sent_count = 0
encoding = "utf-8"
cols = ["verb", "verb_POS", "noun", "noun_POS", "det", "pattern", "count"]
partial_pkl = PARTIAL_FILE.format("pkl")
partial_csv = PARTIAL_FILE.format("csv")


df = pd.DataFrame(columns=cols)

with codecs.open(FILE_PATH, "r", encoding) as infile:
  # read line-by-line from input file
  for line in infile:
    sent_count += 1
    if sent_count % 100 == 0:
      print("Processing sent #{:d}".format(sent_count))
    new_line = line.replace("\n", "").strip()
    # if it is not an empty string, process it
    if new_line != "":
      output = nlp.annotate(new_line, properties)
      # sanity check: if the returned object is a string or a json object
      if isinstance(output, str):
        json_obj = process_json(output, sent_count)
      else:
        json_obj = process_json(json.dumps(output, ensure_ascii=False), sent_count)

      for key in json_obj.keys():
        sent = json_obj[key][0]
        tokens = sent["tokens"]
        deps = sent["basicDependencies"]
        deps_found = process_dependencies(deps, tokens)
        for dep in deps_found:
          v = dep["verb"]
          n = dep["noun"]
          p = dep["pattern"]
          dep["count"] = 1
          d = {
            "verb": dep["verb"],
            "verb_POS": dep["verb_POS"],
            "noun": dep["noun"],
            "noun_POS": dep["noun_POS"],
            "det": dep["det"],
            "pattern": dep["pattern"],
            "count": 1
          }
          df = df.append(d, ignore_index=True)
    if sent_count % 10000 == 0:
      df.to_csv(partial_csv, encoding="utf-8")
      df.to_pickle(partial_pkl)

print("Done!")
print("\n\nSaving dependencies to \n{} \n and {}".format(partial_csv, partial_pkl))
df.to_csv(partial_csv, encoding="utf-8")
df.to_pickle(partial_pkl)
