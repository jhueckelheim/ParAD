from formad.parser import ParloopFinder, ParloopParser, Preprocessor
from formad.analyzer import ParloopAnalyzer
import formad.ompparser as omp
import sys
import json
import re

if __name__ == "__main__":
  if(len(sys.argv)<2):
    raise Exception("Input f90 file must be specified")
  if(len(sys.argv)<3):
    raise Exception("Input JSON file must be specified")
  f90filename = sys.argv[1]
  jsonfilename = sys.argv[2]
  querylinenumber = int(re.findall("questionToZ3_(.*)_line(\d*)\.json", jsonfilename)[0][1])
  adjointstmts = dict()
  questionvars = set()
  with open(jsonfilename, "r") as fp:
    questions = json.load(fp)
    for question in questions:
      varname = question["name"]
      questionvars.add(varname)
      writes = question["write"]
      for write in writes:
        linenumber = write["line"]
        indices = write["idx"]
        statement = "      " + varname + "_b(" + ", ".join(indices) + ") = 0.0\n"
        statement = statement.replace("[","(").replace("]",")")
        if not (linenumber in adjointstmts):
          adjointstmts[linenumber] = []
        adjointstmts[linenumber].append(statement)
    prep = Preprocessor(f90filename, adjointstmts)
    source = prep.source
    parloopFinder = ParloopFinder(source, querylinenumber)
    ompparser = parloopFinder.parser
    parloop = parloopFinder.parloop
    parser = ParloopParser(ompparser, parloop)
    analyzer = ParloopAnalyzer(parloop, parser, questionvars)
    print("{")
    for var in analyzer.safeQueryVars:
      print(f"  \"{var}\": {analyzer.safeQueryVars[var]},")
    print("}")
