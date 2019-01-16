# pyscopad
Python-based automatic differentiation tool for OpenMP pragmas

## What this is about
In reverse-mode automatic differentiation (AD), the data flow of the resulting *adjoint* program is reversed compared to that in the original *primal* program. This means that a parallelisation strategy that works for some program does not work for its adjoint. For each new variable that is created in the adjoint program, `pyscopad` tries to determine the correct scope (shared, private, reduction-add or atomic) to ensure a correct, and hopefully fast, execution.

## Getting started
Two options to see `pyscopad` in action are:

 - type `python pyscopad.py test/stencil.f90`
 - install `pytest` and run it in the pyscopad folder, or see the contents of `test_pyscopad.py`
 
 You will need to install, e.g. using `pip install`:
 - `fparser sympy re operator enum`
 - More information on fparser here: https://github.com/stfc/fparser/

## What's included
`pyscopad` uses the wonderful fparser to parse free-form Fortran files and looks for loops that are OpenMP parallel. It then calls its own lightweight OpenMP parser on that pragma, and its own data flow analyser called *LoopInspector* on the loop body. The results are then combined in the differentiator to determine the appropriate scope for all adjoint variables.

## OpenMP parser
The OpenMP parser barely deserves this name, as it is only a set of regular expressions that look for certain aspects within an OpenMP pragma. It finds the following clauses, and ignores all others:

 - `shared(list)`
 - `private(list)`
 - `reduction(+,list)`
 - `default(none|private|shared)`
 
The parser performs rudimentary sanity checks: Only up to one `default` clause is allowed, and any given variable can appear in at most one clause (e.g. can not be `private` and `shared` at the same time). The parser also has a function that accepts a list of variables, and assigns the correct scope to each, including the `default` scope to all variables that have not been explicitly given one.

## LoopInspector
The LoopInspector traverses the syntax tree of a loop and tries to discover all references to all variables within that loop. All variables that appear on the left hand side of an assignment are added to the set of write accesses, all others are added to the list or read accesses. For each access, the index expression is also saved as a `sympy` expression. For example, the Fortran statement
```
r(i) = r(i) + u(c(j)-1)
```
would add `r(i)` to the set of write expressions, and `i`, `r(i)`, `u(c(j)-1)`, `c(j)`, `j` to the set of read expressions.

After a loop has been analysed fully, LoopInspector offers a number of convenience functions to query the read and write sets. For example, one can check if a certain variable is write-only or read-only. Specific AD-related functions include `LoopInspector.hasSafeReadAccess(var)`, which checks if the adjoint of `var` can safely be made OpenMP `shared`.

## Differentiator
This module applies differentiation rules to an OpenMP pragma, and relies on the analysis and helper functions in LoopInspector to produce more efficient adjoint code.

 ## LoopInspector.hasSafeReadAccess(var)
 This is perhaps the most novel function in `pyscopad`. The adjoint of `var` can be declared OpenMP `shared` if no two threads will attempt to write to it at the same time. This follows if `var` itself is at each index only read by one thread at a time. This follows if the expressions used to index into `var` are a subset of all expressions used to index into any variable while performing write access. For example, consider the following code:
 ```
  !$omp parallel for
  do i=2,n,2
    r(i-1) = 2*u(i)
    r(i) = 3*u(i-1)
  end do
 ```
If this code is free of data races, then no two threads are able to write to the same index in `r`. It follows that `i-1`, `i` on one thread must be distinct from both `i` and `i-1` on any other thread. Since those same expressions are used to read from variable `u`, it follows that `u` has safe read access, and its adjoint can be `shared`.

The same property also allows the analysis of much simpler code, such as
 ```
  !$omp parallel for
  do i=1,n
    r(i) = 2*u(i)
  end do
 ```
 where again, the index expression reading from `u` is a subset of all write index expressions, and therefore the adjoint of `u` can be `shared`.
 
 Future improvements that are planned for `hasSafeReadAccess()` include
  - allowing offsets: If the primal writes to `{i, (1,i), i-1}` and reads from `{i+const, (2,i+const), i-1+const}` (note how `const` is the same in all expressions), then this read access must still be safe.
  - exclusive read access: Use theorem proving, polyhedral model, something else to show that all read index expressions are non-overlapping.
  - slices, strides: It would be nice to support `1:3` etc. as index expressions.
  - nested scopes and writes: If `hasSafeReadAccess` holds within each `if`-block, then it still holds globally. Also, if it holds between writes to variables occuring in index expressions, then it holds globally. With the current implementation, all branches or writes invalidate the analysis.
  - the analysis should be done per subroutine, function, etc.
  
  ## Limitations
Besides the aforementioned limitations of the parser and inspector, pyscopad could be improved in many ways, including:

 - Only OpenMP parallel loops with no synchronisation constructs are supported. More pragmas could be handled, e.g. tasks, targets, atomic, critical, master, ...
 - LoopInspector is written for Fortran, having in mind that all variables are declared outside the parallel loop. For C programs, the scoping rules and analysis must be refined in several ways, to take into account the fact that multiple variables in different parts of the code may have the same name.
 
