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
