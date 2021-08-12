subroutine LBM_SC(srcGrid, dstGrid)
  real, dimension(0:(150)*(1*(120))*(1*(120))*N_CELL_ENTRIES-1) :: srcGrid, dstGrid
  real :: ux, uy, uz, u2, rho
  continue
  !$omp parallel do private( ux, uy, uz, u2, rho ) shared(dstGrid, srcGrid)
  do i = (0)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120))), (0)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+((150))*(1*(120))*(1*(120))), N_CELL_ENTRIES
  !if( iand(srcGrid((FLAGS)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)), OBSTACLE)) then
  !  dstGrid((C)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((C)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((S)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((N)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((N)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((S)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((W)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((E)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((E)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((W)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = srcGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = srcGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((SW)+N_CELL_ENTRIES*((-1)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((NE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((SE)+N_CELL_ENTRIES*((+1)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((NW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((NW)+N_CELL_ENTRIES*((-1)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((SE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((NE)+N_CELL_ENTRIES*((+1)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = srcGrid((SW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((SB)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = srcGrid((NT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((ST)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = srcGrid((NB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((NB)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = srcGrid((ST)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((NT)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = srcGrid((SB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((WB)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = srcGrid((ET)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((WT)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = srcGrid((EB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((EB)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = srcGrid((WT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  dstGrid((ET)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = srcGrid((WB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !  cycle
  !end if

  !rho = + srcGrid((C)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((N)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((S)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((E)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((W)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((NE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((NW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((SE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((SW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((NT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((NB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((ST)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((SB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((ET)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((EB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((WT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !      + srcGrid((WB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))

  !ux = + srcGrid((E)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((W)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((NE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((NW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((SE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((SW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((ET)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((EB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     - srcGrid((WT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((WB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !uy = + srcGrid((N)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((S)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((NE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((NW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     - srcGrid((SE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((SW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((NT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + srcGrid((NB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     - srcGrid((ST)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((SB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))
  !uz = + srcGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((NT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((NB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((ST)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((SB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((ET)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((EB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) &
  !     + srcGrid((WT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) - srcGrid((WB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i))

  !ux = ux / rho
  !uy = uy / rho
  !uz = uz / rho

  !if( iand(srcGrid((FLAGS)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)), ACCEL)) then
  !  ux = 0.005
  !  uy = 0.002
  !  uz = 0.000
  !end if

  u2 = 1.5 * (ux*ux + uy*uy + uz*uz)
  dstGrid((C)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((C)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL1*OMEGA*rho*(1.0 - u2)

  dstGrid((N)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((N)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + uy*(4.5*uy + 3.0) - u2)
  dstGrid((S)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((S)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + uy*(4.5*uy - 3.0) - u2)
  dstGrid((E)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((E)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + ux*(4.5*ux + 3.0) - u2)
  dstGrid((W)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((W)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + ux*(4.5*ux - 3.0) - u2)
  dstGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((T)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + uz*(4.5*uz + 3.0) - u2)
  dstGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((B)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL2*OMEGA*rho*(1.0 + uz*(4.5*uz - 3.0) - u2)

  dstGrid((NE)+N_CELL_ENTRIES*((+1)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((NE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+ux+uy)*(4.5*(+ux+uy) + 3.0) - u2)
  dstGrid((NW)+N_CELL_ENTRIES*((-1)+(+1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((NW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-ux+uy)*(4.5*(-ux+uy) + 3.0) - u2)
  dstGrid((SE)+N_CELL_ENTRIES*((+1)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((SE)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+ux-uy)*(4.5*(+ux-uy) + 3.0) - u2)
  dstGrid((SW)+N_CELL_ENTRIES*((-1)+(-1)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((SW)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-ux-uy)*(4.5*(-ux-uy) + 3.0) - u2)
  dstGrid((NT)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((NT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+uy+uz)*(4.5*(+uy+uz) + 3.0) - u2)
  dstGrid((NB)+N_CELL_ENTRIES*((0)+(+1)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((NB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+uy-uz)*(4.5*(+uy-uz) + 3.0) - u2)
  dstGrid((ST)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((ST)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-uy+uz)*(4.5*(-uy+uz) + 3.0) - u2)
  dstGrid((SB)+N_CELL_ENTRIES*((0)+(-1)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((SB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-uy-uz)*(4.5*(-uy-uz) + 3.0) - u2)
  dstGrid((ET)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((ET)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+ux+uz)*(4.5*(+ux+uz) + 3.0) - u2)
  dstGrid((EB)+N_CELL_ENTRIES*((+1)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((EB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (+ux-uz)*(4.5*(+ux-uz) + 3.0) - u2)
  dstGrid((WT)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(+1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((WT)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-ux+uz)*(4.5*(-ux+uz) + 3.0) - u2)
  dstGrid((WB)+N_CELL_ENTRIES*((-1)+(0)*(1*(120))+(-1)*(1*(120))*(1*(120)))+(i)) = (1.0-OMEGA)*srcGrid((WB)+N_CELL_ENTRIES*((0)+(0)*(1*(120))+(0)*(1*(120))*(1*(120)))+(i)) + DFL3*OMEGA*rho*(1.0 + (-ux-uz)*(4.5*(-ux-uz) + 3.0) - u2)
  end do
end subroutine
