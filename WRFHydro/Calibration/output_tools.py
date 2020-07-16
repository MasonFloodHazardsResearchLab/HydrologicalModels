######################################################################
## Library
from datetime import datetime, timedelta
import glob
import netCDF4
import numpy as np
import os
import pandas as pd
import xarray as xr

######################################################################
## Main

# Extract streamflow from CHANOBS output and save into a csv file
def extract_chanobs1(sim_dir):
    if os.path.exists(f'{sim_dir}/'):
        # Open CHANOBS output files
        nc = xr.open_mfdataset(f'{sim_dir}/*CHANOBS*', concat_dim='time', combine='nested')
        # DataFrame to receive streamflow data
        df = pd.DataFrame()
        for time_step in nc.time:
            j = pd.to_datetime(time_step.values)
            for feature_id in nc.feature_id.values:
                df.loc[j, f'{feature_id}'] = nc.sel(time=time_step,feature_id=feature_id).streamflow
        df.index.names=['datetime_utc']
        # Save DataFrame into csv file
        df.to_csv(f'output_chanobs_{sim_dir}.csv', sep=',') 
        # Close Dataset
        nc.close()



def extract_chanobs2(sim_id_format, fid_list):
    if os.path.exists(f'sim_{sim_id_format}/'):
        # DataFrame to receive streamflow data
        df = pd.DataFrame()
        file_list = glob.glob(f'sim_{sim_id_format}/*CHANOBS_DOMAIN*')
        file_list = sorted(file_list)
        for file_name in file_list:
            ds = xr.open_dataset(file_name)
            a = 5 + len(sim_id_format)
            b = a + 10
            time_step = datetime.strptime(file_name[a:b], '%Y%m%d%H')
            for fid in fid_list:
                df.loc[time_step, f'{fid}'] = ds.sel(feature_id=fid).streamflow
        df.index.names=['datetime_utc']
        # Save DataFrame into csv file
        df.to_csv(f'output_chanobs_sim_{sim_id_format}.csv', sep=',')