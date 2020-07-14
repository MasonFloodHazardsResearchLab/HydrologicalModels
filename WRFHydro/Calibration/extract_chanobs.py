# Library
from datetime import datetime
import glob
import netCDF4
import numpy as np
import pandas as pd
import xarray as xr


# Functions
def truncate(n, decimals=0):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


# Setting
fid_list = [1, 4]   # List of feature ids to be extracted from CHANOBS
sim_start = 1       # Simulation number
sim_end = 32


# Main Code
for sim in range(sim_start, sim_end + 1):
    df = pd.DataFrame()
    sim = '{:02d}'.format(sim)
    file_list = glob.glob(f'sim_{sim}/*CHANOBS_DOMAIN*')
    for file_name in file_list:
        ds = xr.open_dataset(file_name)
        time_step = datetime.strptime(file_name[7:17], '%Y%m%d%H')
        for fid in fid_list:
            value = np.around((ds.sel(feature_id=fid).streamflow)*35.3147,1)
            df.loc[time_step, f'id{fid}_sim{sim}'] = truncate(value,1)
    df.index.names=['datetime_utc']
    df.to_csv(f'sim_{sim}.csv', sep=',')

if sim_end > sim_start:
    sim = '{:02d}'.format(sim_start)
    df = pd.read_csv(f'sim_{sim}.csv', sep=',', 
                     parse_dates=['datetime_utc'], index_col=['datetime_utc'])
    for sim in range(sim_start + 1, sim_end + 1):
        sim = '{:02d}'.format(sim)    
        df_to_add = pd.read_csv(f'sim_{sim}.csv', sep=',', 
                                parse_dates=['datetime_utc'], index_col=['datetime_utc'])
        for col in df_to_add.columns:
            df[f'{col}'] = df_to_add[f'{col}']
    sim_start = '{:02d}'.format(sim_start)
    sim_end = '{:02d}'.format(sim_end)
    df.to_csv(f'sim_{sim_start}_to_{sim_end}.csv', sep=',')
