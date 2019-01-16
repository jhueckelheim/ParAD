# pyscopad
Python-based automatic differentiation tool for OpenMP pragmas

## What this is about
In reverse-mode automatic differentiation (AD), the data flow of the resulting *adjoint* program is reversed compared to that in the original *primal* program. This means that a parallelisation strategy that works for some program does not work for its adjoint. For each new variable that is created in the adjoint program, `pyscopad` tries to determine the correct scope (shared, private, reduction-add or atomic) to ensure a correct, and hopefully fast, execution.

## What's included
`pyscopad` parses Fortran source code written in free-form F90, F2003 or similar, and looks for loops that are OpenMP parallel. It then calls its own lightweight OpenMP parser on that pragma, and its own data flow analyser called *LoopInspector* on the loop body. The results are then combined in the differentiator to determine the appropriate scope for all adjoint variables.

## OpenMP parser
The OpenMP parser barely deserves this name, as it is only a set of regular expressions that look for certain aspects within an OpenMP pragma. It finds the following clauses, and ignores all others:

 - `shared(list)`
 - `private(list)`
 - `reduction(+,list)`
 - `default(none|private|shared)`
 
The parser performs rudimentary sanity checks: Only up to one default clause is allowed, and any given variable can appear in at most one clause (e.g. can not be private and shared at the same time). The parser also has a module that accepts a list of all variables that were found by LoopInspector, and assigns the default scope to all variables that have not been explicitly given a scope within the pragma.

## LoopInspector
The LoopInspector traverses the syntax tree of a loop and tries to discover all references to all variables within that loop. All variables that appear on the left hand side of an assignment are added to the set of write accesses, all others are added to the list or read accesses. For each access, the index expression is also saved as a `sympy` expression. For example, the Fortran statement
```
r(i) = r(i) + u(c(j)-1)
```
would add `r(i)` to the set of write expressions, and `i`, `r(i)`, `u(c(j)-1)`, `c(j)`, `j` to the set of read expressions.

After a loop has been analysed fully, LoopInspector offers a number of convenience functions to query the read and write sets. For example, one can check if a certain variable is write-only or read-only. Specific AD-related functions include `LoopInspector.hasSafeReadAccess(var)`, which checks if the adjoint of `var` can safely be made OpenMP `shared`.

## Differentiator
This module applies differentiation rules to an OpenMP pragma, and relies on the analysis and helper functions in LoopInspector to produce more efficient adjoint code.

## Limitations
Besides the aforementioned limitations of the OpenMP parser, pyscopad could be improved in many ways:

 - Only OpenMP parallel loops with no synchronisation constructs are supported. More pragmas could be handled, e.g. tasks, targets, atomic, critical, master, ...
 - LoopInspector does not currently try to prove or use the *exclusive read property* as described in previous literature. It relies only on symmetric read access, read-only and write-only properties.
 - LoopInspector gives up when arrays are accessed in slices, as in `u(1:3)`.
 - LoopInspector ignores the presence of branches, and subroutine and function calls with side-effects, and the generated adjoint pragmas may be unsafe in such cases.
 - LoopInspector is written for Fortran, having in mind that all variables are declared outside the parallel loop. For C programs, the scoping rules and analysis must be refined in several ways, to take into account the fact that multiple variables in different parts of the code may have the same name.
