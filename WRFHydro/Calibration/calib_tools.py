# Tools for Hydrologic Models Calibration
# Author: Gustavo Coelho
# Jul, 2020

# Library
import math
import numpy as np
import pandas as pd



##################################################################
# Dynamically Dimensioned Search (DDS) Algorithm 
# Tolson and Shoemaker (2007)
##################################################################

def dss_sel(i, m, r, df_dvars):
    
    # STEP 3
    # Probability each decision variable is included in {N}
    prob_i = 1-math.log(i)/math.log(m)
    #print(f'P(i) = {prob_i}')

    # Randomly select J of the D decision variables for inclusion in neighborhood {N}
    sel = [0] * len(df_dvars)
    N = []
    for d in range(0, len(df_dvars)):
        sel[d] = np.random.choice([1,0], 1, p=[prob_i, 1-prob_i])[0]
        if sel[d] == 1:
            #N.append(df_dvars.loc[d, 'x_names'])
            N.append(d)
    #print(f'sel = {sel}')

    # Select one random d for {N} if {N} is empty
    if len(N) < 1:
        N.append(np.random.choice(df_dvars.x_names, 1)[0])
    #print(f'N = {N}')

    # STEP 4
    # Set new values for selected parameters
    x_new = x_best
    #print(f'x_best = {x_best}')
    for j in N:
        xj_min = df_dvars.loc[j, 'x_min']
        xj_max = df_dvars.loc[j, 'x_max']
        xj_best = x_best[j]
        sigj = r * (xj_max - xj_min)
        x_new[j] = xj_best + (sigj * np.random.normal(1))
        if x_new[j] < xj_min:
            x_new[j] = xj_min + (xj_min - x_new[j])
            if x_new[j] > xj_max:
                x_new[j] = xj_min
        if x_new[j] > xj_max:
            x_new[j] = xj_max - (x_new[j] - xj_max)
            if x_new[j] < xj_min:
                x_new[j] = xj_max
    #print(f'x_new = {x_new}')
   
    return x_new



##################################################################
# Metrics
##################################################################

# Example Data
#m = np.array([1, 2, 4, 5, 4, 3, 2, 1])                  # modeled
#o = np.array([1.5, 2.4, 4.8, 5.7, 4.4, 3.8, 2.0, 1.3])  # observed
#n = len(obs)


# Nash-Sutcliffe Efficiency Coefficient (NSE)
def nse(m, o):
    err1 = sum((m - o)**2)
    err2 = sum((o - o.mean())**2)
    nse = 1 - (err1/err2)
    return nse


# Log NSE
def nselog(m, o):
    mlog = np.log10(m)
    olog = np.log10(o)
    err1 = sum((mlog - olog)**2)
    err2 = sum((olog - olog.mean())**2)
    nselog = 1 - (err1/err2)
    return nselog


# Weighted NSE LogNSE
def nsewt(m, o, w):
    if w < 0 or w >1:
        print('NSE Weigth (w) must be in between 0 and 1')
    else:   
        # NSE
        err1 = sum((m - o)**2)
        err2 = sum((o - o.mean())**2)
        nse = 1 - (err1/err2)
        # Log NSE
        mlog = np.log10(m)
        olog = np.log10(o)
        err1 = sum((mlog - olog)**2)
        err2 = sum((olog - olog.mean())**2)
        nselog = 1 - (err1/err2)
        # Weighted mean
        nsewt = ((w * nse) + ((1-w) * nselog)) / 2
    return nsewt 


# Pearson Correlation
def pearson(m, o, n):
    sxy = sum(o * m)
    sx_sy = sum(o) * sum(m)
    s_x2 = sum(o**2)
    s_y2 = sum(m**2)
    sx_2 = sum(o)**2
    sy_2 = sum(m)**2
    pearson = ((n*sxy) - (sx_sy)) / math.sqrt(((n*s_x2)-(sx_2))*((n*s_y2)-(sy_2)))
    return pearson


# Root Mean Square Error (RMSE)
def rmse(m, o, n):
    rmse = math.sqrt(sum((m - o)**2)/n)
    return rmse


# Percent Bias
def pbias(m, o):
    pbias = (sum(m - o) / sum(o)) * 100
    return pbias


# Kling-Gupta Efficiency (KGE)
def kge(m, o, sr=1, sa=1, sb=1):
    r = pearson(m, o, n)
    alpha = m.std() / o.std()
    beta = m.mean() / o.mean()
    # Euclidian distance
    ed = math.sqrt(((sr*(r-1))**2) + ((sa*(alpha-1))**2) + ((sb*(beta-1))**2))
    # Kling-Gupta Efficiency
    kge = 1 - ed
    return kge
