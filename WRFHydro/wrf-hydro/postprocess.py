
import pathlib as pl
import pandas as pd
import numpy as np
import xarray as xr

'''
this library is a customized library for wrf-hydro (and related models)
to combine and post process the results

sort_file_by_time and open_wh_dataset functions are from NCAR 
wrf_hydro_py library https://github.com/NCAR/wrf_hydro_py



'''

def sort_files_by_time(file_list: list):
    """Given a list of file paths, sort list by file modified time
    Args:
        file_list: The list of file paths to sort
    Returns: A list of file paths sorted by file modified time
    """
    file_list_sorted = sorted(
        file_list,
        key=lambda file: file.stat().st_mtime_ns
    )

    return file_list_sorted



def open_wh_dataset(paths: list,
                    chunks: dict = None,
                    forecast: bool = True) -> xr.Dataset:
    """Open a multi-file wrf-hydro output dataset
    Args:
        paths: List ,iterable, or generator of file paths to wrf-hydro netcdf output files
        chunks: chunks argument passed on to xarray DataFrame.chunk() method
        forecast: If forecast the reference time dimension is retained, if not then
        reference_time dimension is set to a dummy value (1970-01-01) to ease concatenation
        and analysis
    Returns:
        An xarray dataset of dask arrays chunked by chunk_size along the feature_id
        dimension concatenated along the time and
        reference_time dimensions
    """

    # Create dictionary of forecasts, i.e. reference times
    ds_dict = dict()
    for a_file in paths:
        ds = xr.open_dataset(a_file, chunks=chunks, mask_and_scale=False)
        # Check if forecast and set reference_time to zero if not
        if not forecast:
            ds.coords['reference_time'].values = np.array(
                [np.datetime64('1970-01-01T00:00:00', 'ns')])

        ref_time = ds['reference_time'].values[0]
        if ref_time in ds_dict:
            # append the new number to the existing array at this slot
            ds_dict[ref_time].append(ds)
        else:
            # create a new array in this slot
            ds_dict[ref_time] = [ds]

    # Concatenate along time axis for each forecast
    forecast_list = list()
    for key in ds_dict.keys():
        forecast_list.append(xr.concat(ds_dict[key],
                                       dim='time',
                                       coords='minimal'))

    # Concatenate along reference_time axis for all forecasts
    wh_dataset = xr.concat(
        forecast_list,
        dim='reference_time',
        coords='minimal'
    )

    # Break into chunked dask array
    if chunks is not None:
        wh_dataset = wh_dataset.chunk(chunks=chunks)

    return wh_dataset



