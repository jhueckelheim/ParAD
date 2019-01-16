import pyscopad
import ompparser

def diffSingleLoopFile(f2003_source):
  parloops = pyscopad.getparloops_string(f2003_source)
  assert(len(parloops)== 1)
  return pyscopad.diffparloop(parloops[0])

def test_explicitscopes():
  f2003_source ="""
subroutine stencil_explicitscopes(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for shared(r, n, u) private(i) default(none)
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))

def test_defaults():
  f2003_source ="""
subroutine stencil_explicitscopes(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))

def test_increment():
  f2003_source ="""
subroutine stencil_increment(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = r(i) + u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))

def test_onetoone():
  f2003_source ="""
subroutine stencil_onetoone(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = 2*u(i)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == ompparser.Scopes.shared)

def test_offset():
  f2003_source ="""
subroutine stencil_offset(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-11
    r(i) = u(i+10)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))

def test_symmetric():
  f2003_source ="""
subroutine stencil_symmetric(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n,2
    r(i-1) = 2*u(i)
    r(i) = 3*u(i-1)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == ompparser.Scopes.shared)

def test_indirect():
  f2003_source ="""
subroutine stencil_indirect(r, u, n, c)
  integer :: n, i
  double precision, dimension(n) :: u, r
  integer, dimension(n) :: c
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n,2
    r(c(i)) = 2*u(c(i-1))
    r(c(i-1)) = 3*u(c(i))
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == ompparser.Scopes.shared)

def test_indirect_nonconst():
  f2003_source ="""
subroutine stencil_indirect_nonconst(r, u, n, c)
  integer :: n, i
  double precision, dimension(n) :: u, r
  integer, dimension(n) :: c
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n,2
    r(c(i)) = 2*u(c(i-1))
    c(i-1) = 4
    r(c(i-1)) = 3*u(c(i))
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))

def test_readwrite():
  f2003_source ="""
subroutine stencil_readwrite(u, n, a)
  integer :: n, i
  double precision, dimension(2,n) :: u
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    u(1,i) = u(2,i-1) + u(2,i+1) -2*u(2,i) * a
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["u"] == ompparser.Scopes.atomic_add)

def test_slice():
  f2003_source ="""
subroutine stencil_slice(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = 2*u(i:i+1)
  end do
end subroutine
"""
  scopes, scopes_b = diffSingleLoopFile(f2003_source)
  assert(scopes["i"] == ompparser.Scopes.private and
         scopes["n"] == ompparser.Scopes.shared  and
         scopes["u"] == ompparser.Scopes.shared  and
         scopes["r"] == ompparser.Scopes.shared  and
         scopes_b["i"] == ompparser.Scopes.private and
         scopes_b["r"] == ompparser.Scopes.shared  and
         scopes_b["u"] == (ompparser.Scopes.reduction_add, ompparser.Scopes.atomic_add))
