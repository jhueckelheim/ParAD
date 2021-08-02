from formad.parser import ParloopFinder, ParloopParser
from formad.analyzer import ParloopAnalyzer
from formad.differentiator import ParloopDifferentiator
import sys

if __name__ == "__main__":
  if(len(sys.argv)<2):
    raise Exception("Input f90 file must be specified")
  filename = sys.argv[1]
  parloopFinder = ParloopFinder(filename)
  for parloop in parloopFinder.parloops:
    parser = ParloopParser(parloop)
    analyzer = ParloopAnalyzer(parloop, parser)
    differentiator = ParloopDifferentiator(analyzer)
    clauses = analyzer.clauses
    clauses_b = differentiator.clauses
    print(parloop)
    print("Original clauses:")
    for varname,clause in clauses.items():
      print("%s: %s"%(varname,clause))
    print("Diff clauses:")
    for varname,clause in clauses_b.items():
      print("%s: %s"%(varname,clause))
    print("\n")

    for var in parser.vars:
      print(str(parser.vars[var]))
