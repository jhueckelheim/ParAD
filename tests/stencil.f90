subroutine stencil_nodefault(res, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for shared(r, n, u) private(i) default(none)
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine

subroutine stencil_default(res, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    r(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine

subroutine stencil_problem(u, n)
  integer :: n, i
  double precision, dimension(2,n) :: u
  !---------------------------------------
  continue
  !$omp parallel for
  do i=2,n-1
    u(1,i) = u(2,i-1) + u(2,i+1) -2*u(2,i)
  end do
end subroutine
