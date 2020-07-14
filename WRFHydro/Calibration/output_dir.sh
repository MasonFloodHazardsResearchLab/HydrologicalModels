#!/bin/bash

new_dir=$1

mkdir ${new_dir}

# CHANOBS files to move
mv *.CHANOBS_DOMAIN* ${new_dir}

# Simulations files to remove
rm *.LDASOUT_DOMAIN*
rm RESTART.2*
rm HYDRO_RST.2*
rm run.log
rm diag_hydro.00*
