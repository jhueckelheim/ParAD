subroutine stencil_nodefault(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for shared(r, n, u) private(i) default(none)
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine

subroutine stencil_default(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine

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

subroutine stencil_trivial(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = 2*u(i)
  end do
end subroutine

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

subroutine stencil_readwrite(u, n)
  integer :: n, i
  double precision, dimension(2,n) :: u
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    u(1,i) = u(2,i-1) + u(2,i+1) -2*u(2,i)
  end do
end subroutine

subroutine call_all(ra, rb, rc, rd, re, u, ubig, n)
  integer :: n
  double precision, dimension(n) :: u, ra, rb, rc, rd, re
  double precision, dimension(2,n) :: ubig
  !---------------------------------------
  call stencil_nodefault(ra, u, n)
  call stencil_default(rb, u, n)
  call stencil_increment(rc, u, n)
  call stencil_trivial(rd, u, n)
  call stencil_symmetric(re, u, n)
  call stencil_readwrite(ubig, n)
end subroutine
