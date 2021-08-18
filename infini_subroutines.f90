! Collection of subroutines to rotate and translate monitoring data xy coords 
! and bin them into voxels.
! Compiled by f2py, outputting a .pyd file which is then called from a wrapper python script.
!-----------------------------------------------------------------------------
!
!the comment lines below beginning with !f2py, inputs: and outputs: are special comments
!read by the compiler, or the wrapper (not sure which) so MUST be retained and correct
!-----------------------------------------------------------------------------
! RJW, Imperial College London, Apr 2021 
!
!
SUBROUTINE binInfini(array_x, array_y, x_pos, y_pos, PD1, PD2, bin_size, binned_stats)
    ! Inputs: array_x, array_y --> dimensions of the declared voxel space
    !         x_pos, y_pos     --> xy laser position vectors
    !         PD1, PD2         --> Photodiode data vectors
    !         bin_size         --> Size of the voxel bins
    ! Outputs: binned_stats --> 10*m*n arrays of binned photodiode data.

    INTEGER :: array_x, array_y,x,y
    INTEGER, DIMENSION(:) :: PD1, PD2  !can I do this to pass variable length arrays??
    REAL, DIMENSION(:) :: x_pos, y_pos
    !local vars
    REAL, DIMENSION(12,array_x, array_y) :: binned_stats
	!key 1 = PD1, 2 = PD2, 3 = STD1, 4 = STD4, 5 = Range 1, 6 = Range 2, 7 = Max 1, 8=Max2, 9=Min1, 10=Min2 
    REAL :: lower_x, upper_x, lower_y, upper_y, bin_size
    INTEGER, ALLOCATABLE :: poi1(:), poi2(:) 
    
    !f2py INTENT(in) :: array_x, array_y, array_z, x_pos, y_pos, PD1, PD2, bin_size
    !f2py INTENT(hide) :: lower_x, upper_x, lower_y, upper_y, poi1(:), poi2(:)
    !f2py INTENT(out) :: binned_stats

!now start doing the actual programming
    binned_stats=0.0
    
    DO x=1,array_x
			lower_x = (x-1)*bin_size
			upper_x = ((x-1)*bin_size)+bin_size
			
		DO y=1,array_y
			lower_y = (y-1)*bin_size
			upper_y = ((y-1)*bin_size)+bin_size
			
            poi1 = PACK(PD1, (lower_x.LT.x_pos.AND.x_pos.LT.upper_x.AND.lower_y.LT.y_pos.AND.y_pos.LT.upper_y))
            poi2 = PACK(PD2, (lower_x.LT.x_pos.AND.x_pos.LT.upper_x.AND.lower_y.LT.y_pos.AND.y_pos.LT.upper_y))
			
			
            IF (SIZE(poi1.GT.0).GT.(bin_size*500)) THEN
			
			    binned_stats(1,x,y)=SUM(poi1)/SIZE(poi1)	!Mean PD1
			    binned_stats(2,x,y)=SUM(poi2)/SIZE(poi2)	!Mean PD2
			    binned_stats(3,x,y)=SQRT((SUM(poi1**2)-binned_stats(1,x,y))/(SIZE(poi1)))
			    binned_stats(4,x,y)=SQRT((SUM(poi2**2)-binned_stats(2,x,y))/(SIZE(poi2)))
			    binned_stats(5,x,y)=MAXVAL(poi1)-MINVAL(poi1)
	            binned_stats(6,x,y)=MAXVAL(poi2)-MINVAL(poi2)
			    binned_stats(7,x,y)=MAXVAL(poi1)
			    binned_stats(8,x,y)=MINVAL(poi1)
			    binned_stats(9,x,y)=MAXVAL(poi2)
			    binned_stats(10,x,y)=MINVAL(poi2)
			    binned_stats(11,x,y)=SIZE(poi1.GT.0)
			    binned_stats(12,x,y)=SIZE(poi2.GT.0)
			END IF
        END DO
        
    END DO
        
END SUBROUTINE
!! ********************************* Routine to translate xy laser data coords to a local part system **************************************************
SUBROUTINE translatePart(x, y, x_ref, y_ref, scale_factor, x_new, y_new)
    ! Inputs: x, y 		   --> xy coordinate vectors of the laser position
    !         x_ref, y_ref --> reference 0,0 part coordinates, determined on the first rotation layer which is not written in Fortran
    !         
    ! Outputs: x_new, y_new --> xy coordinates of the laser data translated onto local part coordinates and scaled

    REAL, DIMENSION(:) :: x, y
    REAL :: x_ref, y_ref
    INTEGER :: scale_factor
    
    !local vars
    REAL, DIMENSION(SIZE(x)) :: x_new, y_new
    
    !f2py INTENT(in) :: x, y, x_ref, y_ref, scale_factor
    !f2py INTENT(out) :: x_new, y_new
    
    !now start doing the actual programming
    
    x_new=(x-x_ref)/scale_factor
    y_new=(y-y_ref)/scale_factor
        
END SUBROUTINE

!!! ********************************* Routine to rotate xy laser data so part is parallel with xyz axes **************************************************

SUBROUTINE rotateXY(x, y, angle, x_square, y_square)
    ! Inputs: x, y 		   --> xy coordinate vectors of the laser position
    !         angle --> angle of rotation, specified in radians
    !         
    ! Outputs: x_new, y_new --> xy coordinates of the rotated laser

    REAL, DIMENSION(:) :: x, y
    REAL :: angle
    
    !local vars
    REAL, DIMENSION(SIZE(x)) :: x_square, y_square
    
    !f2py INTENT(in) :: x, y, angle
    !f2py INTENT(out) :: x_square, y_square
    
    !now start doing the actual programming
    
    x_square = 0 - COS(angle)*(x - 0) - SIN(angle) * (y - 0)
    y_square = 0 - SIN(angle)*(x - 0) + COS(angle) * (y - 0)
        
END SUBROUTINE

