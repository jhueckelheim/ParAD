subroutine stencil(res, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, res
  !---------------------------------------
  continue
  !$omp
  do i=2,n-1
    res(i) = u(i-1) + u(i+1) -2*u(i)
  end do
end subroutine
