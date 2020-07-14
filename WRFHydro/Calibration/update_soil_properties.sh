#!/bin/bash

# This is a bash script to update soil_properties.nc
# Version 1 	Gustavo Coelho 		Jul, 2020


####################################################
# 0. Settings
####################################################

# etc/bash.bashrc
#intel
export INTEL=/home/admin/work_directory/compilers/intel_build
export PATH=$INTEL/bin:$PATH
export LD_LIBRARY_PATH=$INTEL/lib/intel64_lin:$LD_LIBRARY_PATH
export LIBRARY_PATH=$INTEL/lib/intel64_lin:$LIBRARY_PATH
. $INTEL/bin/ifortvars.sh intel64
. $INTEL/bin/iccvars.sh intel64
. $INTEL/bin/compilervars.sh intel64
#HDF5
export H5DIR=/usr/local
export PATH=$H5DIR/bin:$PATH
export LD_LIBRARY_PATH=$H5DIR/lib:$LD_LIBRARY_PATH
#Curl
export ODIR=/home/admin/work_directory/compilers/with_intel/curl_build
export PATH=$ODIR/bin:$PATH
export LD_LIBRARY_PATH=$ODIR/lib:$LD_LIBRARY_PATH
#netcdfc
export NCDIR=/usr/local
export PATH=$NCDIR/bin:$PATH
export LD_LIBRARY_PATH=$NCDIR/lib:$LD_LIBRARY_PATH
export NETCDF=/usr/local
export NETCDF_INC=/usr/local/include
export NETCDF_LIB=/usr/local/lib
#mpich
MPIDIR=/home/admin/work_directory/compilers/with_intel/mpi_build
export PATH=$MPIDIR/bin:$PATH
export LD_LIBRARY_PATH=$MPIDIR/lib:$LD_LIBRARY_PATH
export PKG_CONFIG_PATH=$MPIDIR/lib/pkgconfig:$PKG_CONFIG_PATH
NDIR=/home/admin/work_directory/compilers/with_intel/nf_nc_build
export LD_LIBRARY_PATH=$NDIR/lib:$LD_LIBRARY_PATH


# NCL Tools
export NCAP2=/home/admin/anaconda3/envs/ncl_stable/bin/ncap2
export NCDUMP=/home/admin/anaconda3/envs/ncl_stable/bin/ncdump


####################################################
# 1. Main
####################################################

param_name=$1
param_type=$2 	# 0 = constant or 1 = multiplier
param_value=$3

if [[ param_type -eq 0 ]] ;then
	# Set constant parameter in soil_properties.nc
	$NCAP2 -O -s "${param_name}=${param_name}*0+${param_value}" DOMAIN/soil_properties.nc DOMAIN/soil_properties.nc
	$NCDUMP -v ${param_name} DOMAIN/soil_properties.nc | tail -n 10

elif [[ param_type -eq 1 ]] ;then
	# Set multiplier parameter in soil_properties.nc
	$NCAP2 -O -s "${param_name}=${param_name}*${param_value}" DOMAIN/soil_properties.nc DOMAIN/soil_properties.nc
	$NCDUMP -v ${param_name} DOMAIN/soil_properties.nc | tail -n 10

fi