# FormAD
Formal Methods and AD: A python-based automatic differentiation tool for OpenMP parallel regions

## What this is about
In reverse-mode automatic differentiation (AD), the data flow of the resulting *adjoint* program is reversed compared to that in the original *primal* program. This means that a parallelisation strategy that works for some program does not work for its adjoint. For each new variable that is created in the adjoint program, `formad` tries to determine the correct scope (shared, private, reduction-add or atomic) to ensure a correct, and hopefully fast, execution.

## Getting started
To use `formad`, make sure you install the prerequisites and call Tapenade (with the -openmp flag). Make sure that the current working directory is the one containing `run_formad.py`.
 
 You will need to install at least the following, e.g. using `pip install`:
 - `fparser sympy re operator enum z3`
 -  Tapenade in the OpenMP development branch, `https://gitlab.inria.fr/tapenade/tapenade/-/tree/feature/openmp2`

## What's included
`formad` uses the wonderful fparser to parse free-form Fortran files and looks for loops that are OpenMP parallel. It then calls its own lightweight OpenMP parser on that pragma, and its own data flow analyser on the loop body. The results are then used to answer queries from Tapenade about the correct scoping of the corresponding adjoint variables.

## OpenMP parser
The OpenMP parser barely deserves this name, as it is only a set of regular expressions that look for certain aspects within an OpenMP pragma. It finds the following clauses, and ignores all others:

 - `shared(list)`
 - `private(list)`
 - `reduction(+,list)`
 - `default(none|private|shared)`
 
The parser performs rudimentary sanity checks: Only up to one `default` clause is allowed, and any given variable can appear in at most one clause (e.g. can not be `private` and `shared` at the same time). The parser also has a function that accepts a list of variables, and assigns the correct scope to each, including the `default` scope to all variables that have not been explicitly given one.

## More information
We have a paper that describes formad in great detail, see the pdf file inside the docs folder.
