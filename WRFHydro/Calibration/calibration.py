# Python script to calibrate WRF-Hydro
# Author: Gustavo Coelho
# Jul, 2020


######################################################################
## Libraries
from datetime import datetime, timedelta
import numpy as np
import os
import pandas as pd
import subprocess

import calib_tools
import output_tools



######################################################################
## DSS input parameters (future calib.parm)
# Neighborhood perturbation size parameter:
r = 0.2  # 0.2 is default
# Maximum number of function evaluations:
m = 50
# Initial solution/simulation:
i_start = 1    # can be used to restart from any simulation
# Number of simulation to stop (last or split)
m_stop = 50



######################################################################
## Open decision variables file (dvars.csv)
df_dvars = pd.read_csv('dvars.csv', sep=',')
df_dvars.drop(df_dvars.index[df_dvars['x_flag'] == 0].tolist(), 
              inplace=True)  # Drop flagged variables (0 = drop, 1 = keep)
df_dvars.reset_index(inplace = True, drop=True) # Reset index



######################################################################
## Open forecast points file (frxt_pts.csv)
frxt_pts = pd.read_csv('frxt_pts.csv')
for row in frxt_pts.index:
    frxt_pts.loc[row, 'USGS_ID'] = '{:08d}'.format(frxt_pts.USGS_ID[row])



######################################################################
## Main 
######################################################################

for i in range(i_start, m_stop):

    # Define simulation directory id and name
    sim_id_format = ('{:0' + str(len(str(m))) + 'd}').format(i)
    sim_dir = f'sim_{sim_id_format}'
    print(f'Processing sim_{sim_id_format}...')

    # Initial solution at i=1 or restart
    if i == 1:
        # Define initial solution
        x_init = np.array(df_dvars.x_ini)
        x_best = x_init
        id_best = sim_id_format
        # Create file to store parameters for each simulation
        df_calib = pd.DataFrame(df_dvars.x_names)
        df_calib['x_best'] = x_best
        df_calib[f'{sim_id_format}'] = x_init
        df_calib.index.names = ['param_id']
        df_calib.to_csv('output_calib_param.csv', sep=',')
        # Create file to store results (objective function and id_best)
        df_summary = pd.DataFrame()
        for usgs_id in frxt_pts.USGS_ID:
            df_summary.loc[usgs_id, f'{sim_id_format}'] = 0
        df_summary.loc['f_x', f'{sim_id_format}'] = 0
        df_summary.loc['f_best', f'{sim_id_format}'] = 0
        df_summary.loc['id_best', f'{sim_id_format}'] = 0
        df_summary.index.names = ['obj_function']
        df_summary.to_csv('output_calib_summary.csv', sep=',')
        
    elif i == i_start and i_start > 1:
        # Restart from saved solution
        df_calib = df_calib.read_csv('output_calib_param.csv', sep=',')
        x_init = np.array(df_calib['x_best'])
        x_best = x_init

    # Calibration parameters 
    if i > 1:
        # Compute new random parameter values using DDS
        x_new = calib_tools.dss_sel(i, m, r, df_dvars, x_best)
        # Update input files with new parameter values
        for j in range(0, len(x_new)):
            xj_name = df_dvars.loc[j, 'x_names']
            xj_type = df_dvars.loc[j, 'x_type']
            xj_value = x_new[j]
            # Update soil_properties.nc
            cmd = f'./update_soil_properties.sh {xj_name} {xj_type} {xj_value}'
            subprocess.call(cmd, shell=True)
                    
    # Run WRF-Hydro
    cmd = './run_WH.sh'
    subprocess.call(cmd, shell=True)
    
    # Reset parameters 
    if i > 1:
        # Reset input files to initial values
        for j in range(0, len(x_new)):
            xj_name = df_dvars.loc[j, 'x_names']
            xj_type = df_dvars.loc[j, 'x_type']
            if xj_type == 0: 
                xj_value = df_dvars.loc[j, 'x_ini']
            elif xj_type == 1:
                xj_value = x_new[j]
            # Reset soil_properties.nc
            cmd = f'./reset_soil_properties.sh {xj_name} {xj_type} {xj_value}'
            subprocess.call(cmd, shell=True)
    
    # Create simulation output directory and move CHANOBS files into it
    cmd = f'./output_dir.sh {sim_dir}'
    subprocess.call(cmd, shell=True)
    
    # Read CHANOBS and save in output_chanobs_sim_dir.csv
    fid_list = frxt_pts.FID.tolist()
    output_tools.extract_chanobs2(sim_id_format, fid_list)
    
    # Read output_chanobs and observed data to create mod and obs
    # Modeled Discharge
    mod_raw = pd.read_csv(f'output_chanobs_{sim_dir}.csv',
                          parse_dates=['datetime_utc'], index_col=['datetime_utc'])
    
    # Analyze each station chosed for calibration
    for row in frxt_pts.index:
        fid = frxt_pts.loc[row, 'FID']
        usgs_id = frxt_pts.loc[row, 'USGS_ID']
        # Observed Discharge (USGS)
        obs_raw = pd.read_csv(f'usgs_{usgs_id}_discharge.csv',
                              parse_dates=['datetime_utc'], index_col=['datetime_utc'])
        # Modeled and Observed Data
        df = pd.DataFrame(mod_raw[f'{fid}'])
        for time_step in df.index:
            if time_step in obs_raw.index:
                df.loc[time_step, 'obs'] = obs_raw.loc[time_step, 'discharge_cms']
            else:
                df.drop(index=time_step, inplace=True)
        mod = np.array(df[f'{fid}'])
        obs = np.array(df['obs'])
        
        # Calculate metrics and save into file
        if i == 1:
            data = {'metrics': ['n', 'nse', 'nselog', 'nsewt', 'pearson', 'rmse', 'pbias', 'kge', 
                                'f_x', 'id_best']}
            df_metrics = pd.DataFrame(data=data)
            df_metrics.set_index('metrics', inplace = True)
            df_metrics['x_best'] = 0
            df_metrics.to_csv(f'output_calib_{usgs_id}.csv', sep=',')
        
        if os.path.exists(f'output_calib_{usgs_id}.csv'):
            df_metrics = pd.read_csv(f'output_calib_{usgs_id}.csv', sep=',', index_col=['metrics'])
        else:
            print(f'Missing: output_calib_{usgs_id}.csv')
        
        n = len(obs)
        w = 0.5
        df_metrics.loc['nse', f'{sim_id_format}'] = n
        # Nash-Sutcliffe Efficiency Coefficient (NSE)
        stat_nse = calib_tools.nse(mod, obs)
        df_metrics.loc['nse', f'{sim_id_format}'] = stat_nse
        stat_nselog = calib_tools.nselog(mod, obs)
        df_metrics.loc['nselog', f'{sim_id_format}'] = stat_nselog
        stat_nsewt = calib_tools.nsewt(mod, obs, w)
        df_metrics.loc['nsewt', f'{sim_id_format}'] = stat_nsewt
        # Pearson Correlation
        stat_pearson = calib_tools.pearson(mod, obs, n)
        df_metrics.loc['pearson', f'{sim_id_format}'] = stat_pearson
        # Root Mean Square Error (RMSE)
        stat_rmse = calib_tools.rmse(mod, obs, n)
        df_metrics.loc['rmse', f'{sim_id_format}'] = stat_rmse
        # Percent Bias
        stat_pbias = calib_tools.pbias(mod, obs)
        df_metrics.loc['pbias', f'{sim_id_format}'] = stat_pbias
        # Kling-Gupta Efficiency (KGE)
        stat_kge = calib_tools.kge(mod, obs, n, sr=1, sa=1, sb=1)
        df_metrics.loc['kge', f'{sim_id_format}'] = stat_kge
        
        
        # Save calibration output objective function and sim_id for the best solution
        if row == 0:
            f_x1 = stat_nsewt

            df_summary = pd.read_csv('output_calib_summary.csv', sep=',', index_col=['obj_function'])
            df_summary.loc[f'{usgs_id}', f'{sim_id_format}'] = f_x1
            df_summary.to_csv('output_calib_summary.csv', sep=',')

        elif row == 1:
            f_x2 = stat_nsewt
            f_x_new = 1 - ((f_x1 + f_x2)/2)
            
            df_summary = pd.read_csv('output_calib_summary.csv', sep=',', index_col=['obj_function']) 
            df_summary.loc[f'{usgs_id}', f'{sim_id_format}'] = f_x2
            df_summary.loc['f_x', f'{sim_id_format}'] = f_x_new

            df_calib = pd.read_csv('output_calib_param.csv', sep=',', index_col=['param_id'])
            
            if i == 1:
                f_best = f_x_new
                id_best = sim_id_format

                df_summary.loc['f_best', f'{sim_id_format}'] = f_best
                df_summary.loc['id_best', f'{sim_id_format}'] = id_best
                
                df_calib['x_best'] = x_best
                df_calib[f'{sim_id_format}'] = x_init

            else:
                if f_x_new <= f_best:
                    f_best = f_x_new
                    id_best = sim_id_format
                    x_best = x_new
                    df_calib['x_best'] = x_best

                df_summary.loc['f_best', f'{sim_id_format}'] = f_best
                df_summary.loc['id_best', f'{sim_id_format}'] = id_best
                
                df_calib[f'{sim_id_format}'] = x_new
            
            df_calib.to_csv('output_calib_param.csv', sep=',')
            df_summary.to_csv('output_calib_summary.csv', sep=',')
            