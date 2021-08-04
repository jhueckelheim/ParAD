subroutine stencil_nodefault(r, u, n)
  integer :: n, i
  double precision, dimension(n) :: u, r
  !---------------------------------------
  continue
  !$omp parallel for
  do i=i1,i2,i3
    r(m) = 2*u(e6(i,j))
    r(m) = 3*u(i-1)
    call foo(u,r,e6)
    do j=j1,j2,j3
      if(cond) then
        r(e1(i,j)) = u(e2(i,j)) 
        r(e3(i,j)) = u(e4(i,j))
      elseif(cond) then
        r(e2(i,j)) = u(j)
      else
        r(e5(i,j)) = u(e6(i,j))
      end if
      r(e7(i,j)) = u(e8(i,j))
    end do

    r(k) = 2*u(e6(i,j))
    r(k) = 3*u(i-1)
    if(some_condition) then
      r(i-1) = 2*u(i)
      r(i) = 3*u(i-1)
    else
      r(i) = 2*v(i)
      r(i) = 3*v(i-1)
    end if
    r(l) = 2*u(e6(i,j))
    r(l) = 3*u(i-1)
  end do
end subroutine
