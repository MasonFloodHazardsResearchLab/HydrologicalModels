#!/bin/bash

echo "Simulation start at $(date)"

# Run WRF-Hydro
echo "Running WRF-Hydro..."
mpirun -np 4 ./wrf_hydro.exe > run.log 2>&1
tail -n 1 run.log

echo "Simulation end at $(date)"

rm RESTART.2*
rm HYDRO_RST.2*
rm diag_hydro.00*


