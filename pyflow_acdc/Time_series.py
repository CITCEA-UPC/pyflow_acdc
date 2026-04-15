# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 15:38:12 2024

@author: BernardoCastro
"""

import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from scipy import stats as st

import time

from .grid_analysis import analyse_grid, grid_state
from .ACDC_PF import AC_PowerFlow, DC_PowerFlow, ACDC_sequential
from .constants import DEFAULT_TOLERANCE, DEFAULT_PF_MAX_ITER, BINARY_THRESHOLD, HOURS_PER_YEAR


# Base __all__ with functions that don't require OPF
__all__ = ['Time_series_PF',
           'TS_ACDC_PF',
           'Time_series_statistics',
           'update_grid_data']

try:
    import pyomo.environ as pyo
    from .ACDC_OPF_NL_model import (
        OPF_create_NLModel_ACDC,
        ExportACDC_NLmodel_toPyflowACDC)
    
    from .ACDC_OPF import (
        pyomo_model_solve,
        OPF_obj,
        OPF_step_results,
        pack_variables,
        Translate_pyf_OPF,
        reset_to_initialize,
        calculate_objective
    )
    pyomo_imp= True
    # Add OPF-dependent functions to __all__ only if pyomo is available
    __all__.extend(['TS_ACDC_OPF', 'results_TS_OPF'])
    
except ImportError:    
    pyomo_imp= False


def find_value_from_cdf(cdf, x):
    for i in range(len(cdf)):
        if cdf[i] >= x:
            return i
    return None

def Time_series_PF(grid):
    if grid.nodes_AC == None:
        print("only DC")
    elif grid.nodes_DC == None:
        print("only AC")
    else:
        print("Sequential")
        grid.TS_ACDC_PF(grid)

def combine_TS(ts_list, rep_year=False):
    """Combines multiple time series while maintaining the order of the input list.
    
    Args:
        ts_list: List of pandas DataFrames to combine, each with index 1-8760
        rep_year: If True, averages data hour by hour across years
        
    Returns:
        DataFrame containing combined or averaged time series data
    """
    # Concatenate DataFrames in order
    # save first 2 rows 
    first_two_rows = [df.iloc[:2] for df in ts_list]
    # just save 1 data frame
    first_two_rows = first_two_rows[0]
    # ignore first two rows
    ts_list = [df.iloc[2:] for df in ts_list] 
    # reset index
    ts_list = [df.reset_index(drop=True) for df in ts_list]
    combined_df = pd.concat(ts_list, axis=0, ignore_index=True)
    combined_df = pd.concat([first_two_rows, combined_df], axis=0, ignore_index=True)
    if rep_year:
        # Standardize all dataframes to 8760 hours
        processed_dfs = []
        for df in ts_list:
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # 'coerce' will convert invalid values to NaN
            if len(df) > HOURS_PER_YEAR:
                # remove 29th feb
                df = df.drop(df.index[1416:1440])
                df = df.reset_index(drop=True)
            elif len(df) < HOURS_PER_YEAR:
                df = df.reindex(range(HOURS_PER_YEAR), method='ffill')
            processed_dfs.append(df)
            
        # Calculate element-wise average across all dataframes
        new_df = pd.concat(processed_dfs).groupby(level=0).mean()
        return new_df, combined_df
    
    return combined_df

def update_grid_data(grid,ts, idx,price_zone_restrictions=False,use_clusters=False,n_clusters=None):
    typ = ts.type
    if use_clusters:
        ts_data = ts.data_clustered[n_clusters]
    else:
        ts_data = ts.data
    # Pre-build dictionaries for fast lookups if not already present
    if not hasattr(grid, 'Price_Zones_dict'):
        grid.Price_Zones_dict = {pz.name: pz for pz in grid.Price_Zones}
    if not hasattr(grid, 'nodes_AC_dict'):
        grid.nodes_AC_dict = {node.name: node for node in grid.nodes_AC}
    if not hasattr(grid, 'nodes_DC_dict'):
        grid.nodes_DC_dict = {node.name: node for node in grid.nodes_DC}    
    if not hasattr(grid, 'RenSource_zones_dict'):
        grid.RenSource_zones_dict = {zone.name: zone for zone in grid.RenSource_zones}
    if not hasattr(grid, 'RenSources_dict'):
        grid.RenSources_dict = {rs.name: rs for rs in grid.RenSources}
    
    if price_zone_restrictions:
        # Using dictionaries to directly access the Price Zone objects
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            if typ == 'a_CG':
                price_zone.a_base = ts_data[idx]
            elif typ == 'b_CG':
                price_zone.b = ts_data[idx]
            elif typ == 'c_CG':
                price_zone.c = ts_data[idx]
            elif typ == 'PGL_min':
                price_zone.PGL_min_base = ts_data[idx]
            elif typ == 'PGL_max':
                price_zone.PGL_max = ts_data[idx]
    
    if typ == 'price':
        # Directly access price zone and nodes using dictionaries
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            price_zone.price = ts_data[idx]
        
        node = grid.nodes_AC_dict.get(ts.element_name, None)
        if node:
            node.price = ts_data[idx]
            
        node_dc = grid.nodes_DC_dict.get(ts.element_name, None)
        if node_dc:
            node_dc.price = ts_data[idx]    
    
    elif typ == 'Load':
        # Directly access price zone and nodes using dictionaries
        price_zone = grid.Price_Zones_dict.get(ts.element_name, None)
        if price_zone:
            price_zone.PLi_factor = ts_data[idx]
        
        node = grid.nodes_AC_dict.get(ts.element_name, None)
        if node:
            node.PLi_factor = ts_data[idx]
            
        node_dc = grid.nodes_DC_dict.get(ts.element_name, None)
        if node_dc:
            node_dc.PLi_factor = ts_data[idx]    
    
    elif typ in ['WPP', 'OWPP', 'SF', 'REN','Solar']:
        # Directly access RenSource_zones and RenSources using dictionaries
        zone = grid.RenSource_zones_dict.get(ts.element_name, None)
        if zone:
            zone.PRGi_available = ts_data[idx]
        
        rs = grid.RenSources_dict.get(ts.element_name, None)
        if rs:
            rs.PRGi_available = ts_data[idx]

def update_ac_nodes(grid, idx):
    row_data = {'time': idx+1}
    for node in grid.nodes_AC:
        if node.type == 'Slack':
            PGi = (node.P_INJ - node.P_s - node.PGi_ren * node.curtailment + node.PLi).item()
            QGi = node.Q_INJ - node.Q_s - node.Q_s_fx + node.QLi
            if node.S_rating !=0:
                loading = np.sqrt(PGi**2 + QGi**2) / node.S_rating
            else:
                loading = 0
            row_data.update({
                f'Pg_{node.name}': PGi,
                f'Qg_{node.name}': QGi,
                f'Loading_{node.name}': loading
            })
    return row_data

def update_converters(grid, idx):
    row_data = {'time': idx+1}
    for conv in grid.Converters_ACDC:
        S_AC = np.sqrt(conv.P_AC**2 + conv.Q_AC**2)
        P_DC = conv.P_DC
        row_data.update({
            f'Loading_{conv.name}': np.maximum(S_AC, np.abs(P_DC)) * grid.S_base / conv.MVA_max,
            f'{conv.name}_P_DC': P_DC
        })
    return row_data

def calculate_line_loading(grid,idx):
    loadS_AC = np.zeros(grid.Num_Grids_AC)
    loadP_DC = np.zeros(grid.Num_Grids_DC)
    line_data = {'time': idx+1}

    for line in grid.lines_AC:
        G = grid.Graph_line_to_Grid_index_AC[line]
        load = line.apparent_MVA
        loadS_AC[G] += load
        line_data[f'AC_Load_{line.name}'] = line.loading/100
        line_data[f'AC_to_{line.name}']   = np.real(line.toS) * grid.S_base 

    for line in grid.lines_DC:
        G = grid.Graph_line_to_Grid_index_DC[line]
        load = line.apparent_MVA
        loadP_DC[G] += load
        line_data[f'DC_Load_{line.name}'] = line.loading/100
        line_data[f'DC_to_{line.name}']   = line.toP * grid.S_base 

    return line_data, loadS_AC, loadP_DC

def _calculate_line_loading_from_model(grid,model,idx):
    loadS_AC = np.zeros(grid.Num_Grids_AC)
    loadP_DC = np.zeros(grid.Num_Grids_DC)
    line_data = {'time': idx+1}
 
    
    
    if grid.ACmode:
        keys = sorted(model.PAC_from.keys())

        PAC_from = np.array([np.float64(pyo.value(model.PAC_from[k])) for k in keys])
        QAC_from = np.array([np.float64(pyo.value(model.QAC_from[k])) for k in keys])
        PAC_to = np.array([np.float64(pyo.value(model.PAC_to[k])) for k in keys])
        QAC_to = np.array([np.float64(pyo.value(model.QAC_to[k])) for k in keys])

        S_from   =np.sqrt(PAC_from**2+QAC_from**2)
        S_to     =np.sqrt(PAC_to**2+QAC_to**2)
        
        for line in grid.lines_AC:
            G = grid.Graph_line_to_Grid_index_AC[line]
            load = max(abs(S_from[line.lineNumber]), abs(S_to[line.lineNumber]))
            loadS_AC[G] += load
            line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.capacity_MVA
            line_data[f'AC_to_{line.name}']   = PAC_to[line.lineNumber]   * grid.S_base 

        if grid.TEP_AC:    
            lines_AC_TEP = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesACP.items()}
            lines_AC_TEP_fromP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_from.items()}
            lines_AC_TEP_toP = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_to.items()}
            lines_AC_TEP_fromQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_from.items()}
            lines_AC_TEP_toQ = {k: np.float64(pyo.value(v)) for k, v in model.exp_QAC_to.items()}
            lines_AC_TEP_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.exp_PAC_line_loss.items()}
            for line in grid.lines_AC_exp:
                G = grid.Graph_line_to_Grid_index_AC[line]
                l = line.lineNumber
                n_lines_ac = lines_AC_TEP[l]
                line.P_loss = lines_AC_TEP_P_loss[l] * n_lines_ac
                ac_from = (lines_AC_TEP_fromP[l] + 1j*lines_AC_TEP_fromQ[l]) * n_lines_ac
                ac_to = (lines_AC_TEP_toP[l] + 1j*lines_AC_TEP_toQ[l]) * n_lines_ac
                line_data[f'AC_to_{line.name}'] = ac_to
                load = max(abs(ac_from), abs(ac_to))
                loadS_AC[G] += load
                line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.capacity_MVA if line.capacity_MVA > 0 else 0
        if grid.REC_AC:
            lines_AC_REP = {k: np.float64(pyo.value(v)) for k, v in model.rec_branch.items()}
            lines_AC_REC_fromP = {k: {state: np.float64(pyo.value(model.rec_PAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toP = {k: {state: np.float64(pyo.value(model.rec_PAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_fromQ = {k: {state: np.float64(pyo.value(model.rec_QAC_from[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_toQ = {k: {state: np.float64(pyo.value(model.rec_QAC_to[k, state])) for state in model.branch_states} for k in model.lines_AC_rec}
            lines_AC_REC_P_loss = {k: np.float64(pyo.value(v)) for k, v in model.rec_PAC_line_loss.items()}
            
            for line in grid.lines_AC_rec:
                G = grid.Graph_line_to_Grid_index_AC[line]
                l = line.lineNumber
                line.rec_branch = True if lines_AC_REP[l] >= BINARY_THRESHOLD else False
                line.P_loss = lines_AC_REC_P_loss[l]
                state = 1 if line.rec_branch else 0
                ac_from = (lines_AC_REC_fromP[l][state] + 1j*lines_AC_REC_fromQ[l][state])
                ac_to = (lines_AC_REC_toP[l][state] + 1j*lines_AC_REC_toQ[l][state])
                line_data[f'AC_to_{line.name}'] = ac_to
                load = max(abs(ac_from), abs(ac_to))
                loadS_AC[G] += load
                if state == 1:
                    line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.MVA_rating_new 
                else:
                    line_data[f'AC_Load_{line.name}'] = load * grid.S_base / line.MVA_rating


    if grid.DCmode:
        
        PDC_from = {k: np.float64(pyo.value(v)) for k, v in model.PDC_from.items()}
        PDC_to   = {k: np.float64(pyo.value(v)) for k, v in model.PDC_to.items()}
        n_lines_dc = {k: np.float64(pyo.value(v)) for k, v in model.NumLinesDCP.items()}
        for line in grid.lines_DC:
            G = grid.Graph_line_to_Grid_index_DC[line]
            load = max(abs(PDC_from[line.lineNumber]), abs(PDC_to[line.lineNumber])) * n_lines_dc[line.lineNumber]
            loadP_DC[G] += load
            line_data[f'DC_Load_{line.name}'] = load * grid.S_base / line.capacity_MW if line.capacity_MW > 0 else 0
            line_data[f'DC_to_{line.name}']   = PDC_to[line.lineNumber]   * grid.S_base 

    return line_data, loadS_AC, loadP_DC

def calculate_grid_loading(grid, loadS_AC, loadP_DC,idx):
    grid_data_loading = {'time': idx+1}
    total_loading = 0
    total_rating = 0
    if grid.ACmode:
        total_rating += sum(grid.rating_grid_AC)
    if grid.DCmode:
        total_rating += sum(grid.rating_grid_DC)
    if grid.ACmode:
        for g in range(grid.Num_Grids_AC):
            loading = loadS_AC[g] * grid.S_base
            total_loading += loading
            grid_data_loading[f'Loading_Grid_AC_{g+1}'] = 0 if grid.rating_grid_AC[g] == 0 else loading / grid.rating_grid_AC[g]

    if grid.DCmode:
        for g in range(grid.Num_Grids_DC):
            loading = loadP_DC[g] * grid.S_base
            total_loading += loading
            grid_data_loading[f'Loading_Grid_DC_{g+1}'] = loading / grid.rating_grid_DC[g]

    grid_data_loading['Total'] = 0 if total_rating == 0 else total_loading /total_rating
    return grid_data_loading

def calculate_price_zone_price(grid,idx):
    price_zone_price = {'time': idx+1}
    for m in grid.Price_Zones:
         price_zone_price[m.name]=m.price
         
    return price_zone_price

def calculate_price_zone_price_from_model(grid,model,idx):
    price_zone_price = {'time': idx+1}
    prices    = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_price.items()}
    for m in grid.Price_Zones:
         price_zone_price[m.name]=prices[m.price_zone_num]
    
    return price_zone_price


def calculate_pz_social_cost_kEUR_from_model(grid, model, idx):
    """Per price zone social cost of generation in k€ (model SocialCost / 1000), aligned with MS export."""
    row = {'time': idx + 1}
    if not getattr(grid, 'Price_Zones', None) or not hasattr(model, 'SocialCost'):
        return row
    for m in grid.Price_Zones:
        n_m = m.price_zone_num
        sc = np.float64(pyo.value(model.SocialCost[n_m]))
        row[m.name] = np.round(sc / 1000.0, decimals=4)
    return row


def calculate_pz_p_known_mw_from_model(grid, model, idx):
    """
    Per price zone: sum of model P_known (pu) on zone nodes × S_base → MW.
    Same definition as MS export ``PZ_load`` / ``get_price_zone_data`` row_data_load.
    """
    row = {'time': idx + 1}
    if not getattr(grid, 'Price_Zones', None) or not hasattr(model, 'P_known_AC'):
        return row
    for m in grid.Price_Zones:
        load_pu = 0.0
        for node in m.nodes_AC:
            load_pu += pyo.value(model.P_known_AC[node.nodeNumber])
        if grid.DCmode and hasattr(model, 'P_known_DC'):
            for node in m.nodes_DC:
                load_pu += pyo.value(model.P_known_DC[node.nodeNumber])
        row[m.name] = np.round(load_pu * grid.S_base, decimals=2)
    return row


def calculate_net_price_zone_power_from_model(grid, model, idx):
    net_price_zone_power = {'time': idx + 1}
    if hasattr(model, 'PN'):
        pn_values = {k: np.float64(pyo.value(v)) for k, v in model.PN.items()}
        for m in grid.Price_Zones:
            if m.price_zone_num in pn_values:
                net_price_zone_power[m.name] = pn_values[m.price_zone_num] * grid.S_base
    return net_price_zone_power
def calculate_res_available_from_model(grid, model, idx):
    res_available = {'time': idx + 1}
    if hasattr(model, 'ren_sources'):
        res_available_values = {k: np.float64(pyo.value(v)) for k, v in model.P_renSource.items()}
        np_rsgen_values = {k: np.float64(pyo.value(v)) for k, v in model.np_rsgen.items()}
        for rs in grid.RenSources:
            res_available[rs.name] = res_available_values[rs.rsNumber] * np_rsgen_values[rs.rsNumber] * grid.S_base
    return res_available

def calculate_pn_min_max_from_model(grid, model, idx):
    """
    Compute PN lower/upper bounds (MW) from the model's PN bounds.

    In Pyomo these are the price-zone power bounds: model.PGL_min / model.PGL_max.
    They bound model.PN with: PGL_min <= PN <= PGL_max.
    """
    pn_min = {'time': idx + 1}
    pn_max = {'time': idx + 1}
    a = {'time': idx + 1}
    b = {'time': idx + 1}
    if hasattr(model, 'PGL_min') and hasattr(model, 'PGL_max'):
        pgl_min_values = {k: np.float64(pyo.value(v)) for k, v in model.PGL_min.items()}
        pgl_max_values = {k: np.float64(pyo.value(v)) for k, v in model.PGL_max.items()}
        a_values = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_a.items()}
        b_values = {k: np.float64(pyo.value(v)) for k, v in model.price_zone_b.items()}
        for m in grid.Price_Zones:
            # model.PGL_min/max are indexed by price_zone_num
            if m.price_zone_num in pgl_min_values:
                pn_min[m.name] = pgl_min_values[m.price_zone_num] * grid.S_base
            if m.price_zone_num in pgl_max_values:
                pn_max[m.name] = pgl_max_values[m.price_zone_num] * grid.S_base
            if m.price_zone_num in a_values:
                a[m.name] = a_values[m.price_zone_num]
            if m.price_zone_num in b_values:
                b[m.name] = b_values[m.price_zone_num]
    return pn_min, pn_max, a, b


def TS_ACDC_PF(grid, start=1, end=None,print_step=False,tol_lim=DEFAULT_TOLERANCE, maxIter=DEFAULT_PF_MAX_ITER):
    idx = start-1
    TS_len = len(grid.Time_series[0].data)
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)
        
    Time_series_res = []
    Time_series_line_res = []
    Time_series_conv_res = []
    Time_series_grid_loading = []
    analyse_grid(grid)
    # saving droop configuration to reset each time, if not it takes power set from previous point.
    grid.Pconv_save = np.zeros(grid.nconv)
    for conv in grid.Converters_ACDC:
        grid.Pconv_save[conv.ConvNumber] = conv.P_DC
    
    while idx < max_time:
        
  
        for ts in grid.Time_series:
            update_grid_data(grid, ts, idx)
        if grid.ACmode and grid.DCmode:    
            for conv in grid.Converters_ACDC:         
                if conv.type in ['Droop', 'P']:
                    conv.P_DC = grid.Pconv_save[conv.ConvNumber] #This resets the converters droop target
            
            ACDC_sequential(grid,QLimit=False)
        elif grid.ACmode:
            t,tol=AC_PowerFlow(grid,tol_lim, maxIter)
        elif grid.DCmode:
            t,tol=DC_PowerFlow(grid,tol_lim, maxIter)

        with ThreadPoolExecutor() as executor:
            # Submit the functions to the executor
            future_row_data = executor.submit(update_ac_nodes, grid, idx)
            future_line_data = executor.submit(calculate_line_loading, grid, idx)
            if grid.ACmode and grid.DCmode:
                future_conv_data = executor.submit(update_converters, grid, idx)
                conv_data = future_conv_data.result()
            else:
                conv_data = None
            # Wait for the results
            row_data = future_row_data.result()
            line_data, loadS_AC, loadP_DC = future_line_data.result()
            
        grid_data_loading = calculate_grid_loading(grid, loadS_AC, loadP_DC,idx)
        row_data['time'] = idx+1
        Time_series_res.append(row_data)
        if conv_data is not None:
            conv_data['time'] = idx+1
            Time_series_conv_res.append(conv_data)
        line_data['time'] = idx+1
        Time_series_line_res.append(line_data)
        grid_data_loading['time'] = idx+1
        Time_series_grid_loading.append(grid_data_loading)
        
    
        if print_step:
            print(idx+1)
        idx += 1
        
    # Create the DataFrame from the list of rows
    def to_dataframe(data):
        return pd.DataFrame(data).set_index('time')
    grid.time_series_results['PF_results']   = to_dataframe(Time_series_res)
    line_data_df = to_dataframe(Time_series_line_res)
    # Split line time-series into explicit loading and MW-to datasets
    ac_loading = line_data_df.filter(like='AC_Load_', axis=1)
    dc_loading = line_data_df.filter(like='DC_Load_', axis=1)
    ac_mw_to = line_data_df.filter(like='AC_to_', axis=1)
    dc_mw_to = line_data_df.filter(like='DC_to_', axis=1)
    
    # Remove prefixes from column names for both DataFrames
    ac_loading.columns = ac_loading.columns.str.replace('AC_Load_', '', regex=False)
    dc_loading.columns = dc_loading.columns.str.replace('DC_Load_', '', regex=False)
    ac_mw_to.columns = ac_mw_to.columns.str.replace('AC_to_', '', regex=False)
    dc_mw_to.columns = dc_mw_to.columns.str.replace('DC_to_', '', regex=False)

    grid.time_series_results['ac_loading'] = ac_loading
    grid.time_series_results['dc_loading'] = dc_loading
    grid.time_series_results['ac_MW_to'] = ac_mw_to
    grid.time_series_results['dc_MW_to'] = dc_mw_to
    
    if grid.ACmode and grid.DCmode:
        grid.time_series_results['converter_loading'] = to_dataframe(Time_series_conv_res)
    grid.time_series_results['grid_loading'] = to_dataframe(Time_series_grid_loading)
 
    grid.Time_series_ran = True


def _modify_parameters(grid,model,Price_Zones):
    opf_data = Translate_pyf_OPF(grid,Price_Zones=Price_Zones)
    AC_info = opf_data['AC_info']
    DC_info = opf_data['DC_info']
    Price_Zone_info = opf_data['Price_Zone_info']
    gen_info = opf_data['gen_info']    
    ACmode = grid.ACmode
    DCmode = grid.DCmode
    AC_Lists, AC_nodes_info, AC_lines_info,EXP_info,REP_info,CT_info = AC_info
    
    gen_AC_info, gen_DC_info, gen_rs_info = gen_info
    lf,qf,fc,np_gen,lista_gen = gen_AC_info
    P_renSource, np_rsgen, lista_rs = gen_rs_info

    _,_,_,_, P_know,Q_know,price = AC_nodes_info
    if DCmode:
        DC_Lists,DC_nodes_info,_,_ = DC_info
        lf_DC,qf_DC,fc_DC,np_gen_DC,lista_gen_DC = gen_DC_info
        _, _ ,_,P_known_DC,price_dc  = DC_nodes_info

    _,Price_Zone_lim = Price_Zone_info

    price_zone_as,price_zone_bs,PGL_min, PGL_max = Price_Zone_lim
    
    if Price_Zones:
        for idx, val in price_zone_as.items():
            model.price_zone_a[idx].set_value(val)
        for idx, val in price_zone_bs.items():
            model.price_zone_b[idx].set_value(val)
        for idx, val in PGL_min.items():
            model.PGL_min[idx].set_value(val)
        for idx, val in PGL_max.items():
            model.PGL_max[idx].set_value(val)
    else:
        if ACmode:
            for idx, val in price.items():
                model.price[idx].set_value(val)
            for idx, val in lf.items():
                model.lf[idx].set_value(val)
        if DCmode:
            for idx, val in price_dc.items():   
                 model.price_dc[idx].set_value(val)    
            for idx, val in lf_DC.items():
                model.lf_dc[idx].set_value(val)
    
    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)
    
    if ACmode:
        for idx, val in P_know.items():
            model.P_known_AC[idx].set_value(val)
        for idx, val in Q_know.items():
            model.Q_known_AC[idx].set_value(val)
        if hasattr(model, 'P_load_eff'):
            for gen in grid.Generators:
                model.P_load_eff[gen.genNumber].set_value(gen.p_load_eff)
        # Keep ext-grid generator bounds synchronized with scenario/investment load factors
        # when the OPF model is reused across time steps.
        if hasattr(model, 'PGi_gen') and not hasattr(model, 'PGi_lower_bound'):
            for gen in grid.Generators:
                if not getattr(gen, 'is_ext_grid', False):
                    continue
                g = gen.genNumber
                np_gen_value = pyo.value(model.np_gen[g]) if hasattr(model, 'np_gen') else gen.np_gen
                pmax_eff = gen.Max_pow_gen * np_gen_value
                if getattr(gen, 'allow_sell', True):
                    pmin_eff = -(pmax_eff - gen.p_load_eff)
                else:
                    pmin_eff = 0
                model.PGi_gen[g].setlb(pmin_eff)
                model.PGi_gen[g].setub(pmax_eff)
            
    if DCmode:
        for idx, val in P_known_DC.items():
            model.P_known_DC[idx].set_value(val)
    for idx, val in P_renSource.items():
        model.P_renSource[idx].set_value(val)


def TS_ACDC_OPF(
    grid,
    start=1,
    end=None,
    ObjRule=None,
    price_zone_restrictions=False,
    expand=False,
    print_step=False,
    limit_flow_rate=True,
    use_clusters=False,
    n_clusters=None,
    solver='ipopt',
    obj_scaling=1.0,
    warm_start_mode='roll',
    export_to_grid=True,
):
    idx = start-1
    warm_start_mode = str(warm_start_mode).lower()
    if warm_start_mode not in ('roll', 'hard'):
        raise ValueError("warm_start_mode must be either 'roll' or 'hard'")
    TS_len = len(grid.Time_series[0].data)
    total_solve_time  = 0
    total_update_time = 0
    count = 0
    if end is None:
        end = TS_len
    max_time = min(TS_len, end)
    
    Time_series_voltages = []
    Time_series_line_res = []
    Time_series_conv_res = []
    Time_series_grid_loading = []
    
    Time_series_Opt_res_P_conv_AC = []
    Time_series_Opt_res_Q_conv_AC = []
    Time_series_Opt_res_P_conv_DC = []
    Time_series_Opt_res_P_Load    = []
    Time_series_Opt_res_P_extGrid = []
    Time_series_Opt_res_Q_extGrid =[]
    Time_series_Opt_curtailment   =[]
    
    Time_series_price = []
    Time_series_PZ_cost_kEUR = []
    Time_series_PZ_load = []
    Time_series_net_price_zone_power = []
    Time_series_PN_min = []
    Time_series_PN_max = []
    Time_series_a = []
    Time_series_b = []
    Time_series_res_available = []
    
    weights_def = {
       'Ext_Gen': {'w': 0},
       'Energy_cost': {'w': 0},
       'Curtailment_Red': {'w': 0},
       'AC_losses': {'w': 0},
       'DC_losses': {'w': 0},
       'Converter_Losses': {'w': 0},
       'General_Losses': {'w': 0},  
       'PZ_cost_of_generation': {'w': 0},
       'Renewable_profit': {'w': 0},
       'Gen_set_dev': {'w': 0}
    }

    # If user provides specific weights, merge them with the default
    if ObjRule is not None:
       for key in ObjRule:
           if key in weights_def:
               weights_def[key]['w'] = ObjRule[key]

    PV_set=False
    if  weights_def['PZ_cost_of_generation']['w']!=0 :
        price_zone_restrictions=True
    if  weights_def['Curtailment_Red']['w']!=0 :
        grid.CurtCost=True
        
        
    def _snapshot_initial_values(model_obj):
        values = {}
        for var_obj in model_obj.component_objects(pyo.Var, active=True):
            values[var_obj.name] = {index: var_obj[index].value for index in var_obj}
        return values

    def _build_ts_model():
        model_obj = pyo.ConcreteModel()
        model_obj.name = "TS AC/DC hybrid OPF"

        OPF_create_NLModel_ACDC(model_obj,grid,PV_set,price_zone_restrictions,limit_flow_rate=limit_flow_rate)

        obj_rule_local = OPF_obj(model_obj,grid,weights_def,OnlyGen=True)
        if obj_scaling != 1.0:
            obj_rule_local = obj_rule_local / obj_scaling
        model_obj.obj = pyo.Objective(rule=obj_rule_local, sense=pyo.minimize)
        model_obj.obj_scaling = obj_scaling
        return model_obj

    analyse_grid(grid)
    t1 = time.perf_counter()
    model = _build_ts_model()
    t2 = time.perf_counter()
    t_modelcreate = t2 - t1
    initial_values = _snapshot_initial_values(model)
    t_minus_1_values = None

    if expand:
        for price_zone in grid.Price_Zones:
            price_zone.expand_import = True
        
    infeasible= 0
    inf_list=[]
    if not use_clusters:
        n_clusters = 1
    else:
        available_clusters = list(grid.Time_series[0].data_clustered.keys())
        if len(available_clusters) == 0:
            use_clusters = False
            n_clusters = None
            print("No clusters available")
            print("Please run clustering first,running full Time series")
        elif n_clusters is not None:
            if n_clusters not in available_clusters:
                raise ValueError(f"Invalid cluster number {n_clusters}. Available clusters: {available_clusters}")
        elif len(available_clusters) == 1:
            n_clusters = available_clusters[0]
        else:
            raise ValueError(f"Multiple clusters available: {available_clusters}. Pass n_clusters= to select one.")
        max_time  = len(grid.Time_series[0].data_clustered[n_clusters])

    while idx < max_time:
        for ts in grid.Time_series:
            update_grid_data(grid,ts, idx,price_zone_restrictions,use_clusters=use_clusters,n_clusters=n_clusters)
        Total_load, min_generation, max_generation = grid_state(grid)     

        if Total_load < min_generation or Total_load > max_generation:
            print(f"Total load {Total_load} is out of bounds {min_generation} and {max_generation}")
            inf_list.append(idx+1)
            idx += 1
            infeasible += 1
            
            continue
        t1= time.perf_counter()          
        if warm_start_mode == 'hard':
            reset_to_initialize(model, initial_values)
    
        _modify_parameters(grid,model,price_zone_restrictions)
        t2= time.perf_counter()  
        t_modelupdate = t2-t1
        
        results, solver_stats = pyomo_model_solve(model,grid,solver,suppress_warnings=True)
        termination_condition = str((solver_stats or {}).get('termination_condition') or '').lower()
        solution_found = bool((solver_stats or {}).get('solution_found', False))
        if (results is None) or (not solution_found):
            # Retry with opposite initialization strategy for this timestep.
            retry_mode = 'roll' if warm_start_mode == 'hard' else 'hard'
            if print_step:
                print(f"{idx+1} Failed with {warm_start_mode}")
            retry_model = _build_ts_model()
            if retry_mode == 'hard':
                reset_to_initialize(retry_model, initial_values)
            elif t_minus_1_values is not None:
                reset_to_initialize(retry_model, t_minus_1_values)
            _modify_parameters(grid,retry_model,price_zone_restrictions)
            retry_results, retry_stats = pyomo_model_solve(retry_model,grid,solver,suppress_warnings=True)
            retry_solution_found = bool((retry_stats or {}).get('solution_found', False))
            if retry_results is not None and retry_solution_found:
                model = retry_model
                results, solver_stats = retry_results, retry_stats
                if print_step:
                    print(f"{idx+1} Passed with {retry_mode} returning to {warm_start_mode}")
            else:
                infeasible += 1
                inf_list.append(idx+1)
                if print_step:
                    reason = str((retry_stats or {}).get('termination_condition') or termination_condition or 'solver error').lower()
                    print(f"{idx+1} Failed with {retry_mode}")
                    print(f"{idx+1} skipped ({reason})")
                idx += 1
                continue
        t_modelsolve = (solver_stats or {}).get('time')
        if t_modelsolve is None:
            t_modelsolve = 0.0
        
        total_update_time+= t_modelupdate
        total_solve_time += t_modelsolve
      
        count += 1
        [opt_res_P_conv_DC, opt_res_P_conv_AC, opt_res_Q_conv_AC, opt_P_load,opt_res_P_extGrid, opt_res_Q_extGrid, opt_res_curtailment,opt_res_Loading_conv] = OPF_step_results(model,grid)
                 
        
        opt_res_curtailment['time'] = idx+1
        opt_res_P_conv_AC['time'] = idx+1
        opt_res_Q_conv_AC['time'] = idx+1
        opt_res_P_conv_DC['time'] = idx+1
        opt_P_load['time']        = idx+1
        opt_res_P_extGrid['time'] = idx+1
        opt_res_Q_extGrid['time'] = idx+1
        opt_res_Loading_conv['time'] = idx+1
        

        line_data, loadS_AC, loadP_DC = _calculate_line_loading_from_model( grid, model,idx)
        
        
        grid_data_loading = calculate_grid_loading(grid, loadS_AC, loadP_DC,idx)
        
        if price_zone_restrictions:
            price_zone_price = calculate_price_zone_price_from_model(grid,model,idx)
            net_price_zone_power = calculate_net_price_zone_power_from_model(grid, model, idx)
        else:
            price_zone_price = calculate_price_zone_price(grid,idx)
            net_price_zone_power = {'time': idx + 1}

        pz_cost_kEUR = calculate_pz_social_cost_kEUR_from_model(grid, model, idx)
        pz_load_mw = calculate_pz_p_known_mw_from_model(grid, model, idx)

        pn_min, pn_max, a, b = calculate_pn_min_max_from_model(grid, model, idx)

        res_available = calculate_res_available_from_model(grid, model, idx)
        
        Time_series_price.append(price_zone_price)
        Time_series_PZ_cost_kEUR.append(pz_cost_kEUR)
        Time_series_PZ_load.append(pz_load_mw)
        Time_series_net_price_zone_power.append(net_price_zone_power)
        Time_series_PN_min.append(pn_min)
        Time_series_PN_max.append(pn_max)
        Time_series_a.append(a)
        Time_series_b.append(b)
        Time_series_res_available.append(res_available)
        Time_series_conv_res.append(opt_res_Loading_conv)
        Time_series_line_res.append(line_data)
        Time_series_grid_loading.append(grid_data_loading)
            
 
        Time_series_Opt_res_P_conv_AC.append(opt_res_P_conv_AC)
        Time_series_Opt_res_Q_conv_AC.append(opt_res_Q_conv_AC)
        Time_series_Opt_res_P_conv_DC.append(opt_res_P_conv_DC)
        Time_series_Opt_res_P_Load.append(opt_P_load)
        Time_series_Opt_res_P_extGrid.append(opt_res_P_extGrid)
        Time_series_Opt_res_Q_extGrid.append(opt_res_Q_extGrid)
        Time_series_Opt_curtailment.append(opt_res_curtailment)
        t_minus_1_values = _snapshot_initial_values(model)
        
        if print_step:
            print(idx+1)
        idx += 1
    
    
    if export_to_grid:
        t1 = time.perf_counter()
        ExportACDC_NLmodel_toPyflowACDC(model, grid, price_zone_restrictions)
        for obj in weights_def:
            weights_def[obj]['v'] = calculate_objective(grid, obj)
        t2 = time.perf_counter()
        t_modelexport = t2 - t1
    else:
        t_modelexport = 0.0

    # Persist timestep indices that failed / were skipped during the TS loop.
    # These are 1-based indices (matching the public TS time step numbering).
    grid.ts_infeasible_indices = sorted(set(inf_list))
    ts_results = pack_variables(Time_series_conv_res,Time_series_line_res,Time_series_grid_loading,
                            Time_series_Opt_res_P_conv_AC,Time_series_Opt_res_Q_conv_AC,Time_series_Opt_res_P_conv_DC,
                            Time_series_Opt_res_P_extGrid,Time_series_Opt_res_Q_extGrid,Time_series_Opt_curtailment,
                            Time_series_Opt_res_P_Load,Time_series_price,Time_series_PZ_cost_kEUR,Time_series_PZ_load,Time_series_net_price_zone_power,
                            Time_series_PN_min,Time_series_PN_max,Time_series_a,Time_series_b,Time_series_res_available)
    
    av_t_modelsolve = total_solve_time / count if count else 0.0
    av_t_modelupdate=total_update_time / count if count else 0.0
    
    # Always persist time-series result frames for plotting/reporting.
    # export_to_grid only controls whether final model state is written back to grid objects.
    save_TS_to_grid(grid, ts_results, infeasible)
    grid.OPF_obj = weights_def
    grid.OPF_run = True
    grid.Time_series_ran = True
    
    
    
    
    timing_info = {
    "Create": t_modelcreate,
    "Update model Avg": av_t_modelupdate,
    "Solve model Avg": av_t_modelsolve,
    "Export": t_modelexport,
    }
    
    return timing_info


def save_TS_to_grid (grid,ts_results,infeasible):
    # Create the DataFrame from the list of rows
    (Time_series_conv_res,Time_series_line_res,Time_series_grid_loading,
    Time_series_Opt_res_P_conv_AC,Time_series_Opt_res_Q_conv_AC,Time_series_Opt_res_P_conv_DC,
    Time_series_Opt_res_P_extGrid,Time_series_Opt_res_Q_extGrid,Time_series_Opt_curtailment,
    Time_series_Opt_res_P_Load,Time_series_price,Time_series_PZ_cost_kEUR,Time_series_PZ_load,Time_series_net_price_zone_power,
    Time_series_PN_min,Time_series_PN_max,Time_series_a,Time_series_b,Time_series_res_available)= ts_results

    def to_dataframe(data):
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()
        if 'time' in df.columns:
            return df.set_index('time')
        return df
    
    grid.time_series_results['converter_p_dc'] = to_dataframe(Time_series_Opt_res_P_conv_DC)
    grid.time_series_results['converter_q_ac'] = to_dataframe(Time_series_Opt_res_Q_conv_AC)
    grid.time_series_results['converter_p_ac'] = to_dataframe(Time_series_Opt_res_P_conv_AC)
    grid.time_series_results['converter_loading'] = to_dataframe(Time_series_conv_res)
    
    grid.time_series_results['real_load_opf'] = to_dataframe(Time_series_Opt_res_P_Load)
    grid.time_series_results['real_power_opf'] = to_dataframe(Time_series_Opt_res_P_extGrid)
    grid.time_series_results['reactive_power_opf'] = to_dataframe(Time_series_Opt_res_Q_extGrid)
   
    grid.time_series_results['curtailment'] = to_dataframe(Time_series_Opt_curtailment)
   
    line_data_df = to_dataframe(Time_series_line_res)
    grid.time_series_results['grid_loading'] = to_dataframe(Time_series_grid_loading)
    
    grid.time_series_results['prices_by_zone'] = to_dataframe(Time_series_price)
    grid.time_series_results['PZ_cost_of_generation'] = to_dataframe(Time_series_PZ_cost_kEUR)
    grid.time_series_results['PZ_load'] = to_dataframe(Time_series_PZ_load)
    grid.time_series_results['net_price_zone_power'] = to_dataframe(Time_series_net_price_zone_power)
    grid.time_series_results['PZ_lb'] = to_dataframe(Time_series_PN_min)
    grid.time_series_results['PZ_ub'] = to_dataframe(Time_series_PN_max)
    grid.time_series_results['a'] = to_dataframe(Time_series_a)
    grid.time_series_results['b'] = to_dataframe(Time_series_b)
    grid.time_series_results['res_available'] = to_dataframe(Time_series_res_available)
    # Split line time-series into explicit loading and MW-to datasets
    ac_loading = line_data_df.filter(like='AC_Load_', axis=1)
    dc_loading = line_data_df.filter(like='DC_Load_', axis=1)
    ac_mw_to = line_data_df.filter(like='AC_to_', axis=1)
    dc_mw_to = line_data_df.filter(like='DC_to_', axis=1)
    
    # Remove prefixes from column names for both DataFrames
    ac_loading.columns = ac_loading.columns.str.replace('AC_Load_', '', regex=False)
    dc_loading.columns = dc_loading.columns.str.replace('DC_Load_', '', regex=False)
    ac_mw_to.columns = ac_mw_to.columns.str.replace('AC_to_', '', regex=False)
    dc_mw_to.columns = dc_mw_to.columns.str.replace('DC_to_', '', regex=False)

    grid.time_series_results['ac_loading'] = ac_loading
    grid.time_series_results['dc_loading'] = dc_loading
    grid.time_series_results['ac_MW_to'] = ac_mw_to
    grid.time_series_results['dc_MW_to'] = dc_mw_to
    

    for line in (grid.lines_AC + grid.lines_AC_tf + grid.lines_AC_rec + grid.lines_AC_exp):
        col = line.name
        if col in ac_loading:
            max_frac = float(ac_loading[col].max())
            avg_frac = float(ac_loading[col].mean())
            setattr(line, 'ts_max_loading', max_frac*100)   
            setattr(line, 'ts_avg_loading', avg_frac*100)    # fraction of rating (0..)
            

    # DC lines
    for line in grid.lines_DC:
        col = line.name
        if col in dc_loading:
            max_frac = float(dc_loading[col].max())
            avg_frac = float(dc_loading[col].mean())
            setattr(line, 'ts_max_loading', max_frac*100)
            setattr(line, 'ts_avg_loading', avg_frac*100)

            
    grouped_columns_load = {}
    grouped_columns = {}   
    # Group columns based on prefix in external generation data
    
    for col in grid.time_series_results['real_load_opf'].columns:
         prefix = ''.join(filter(str.isalpha, col))
         if prefix not in grouped_columns_load:
             grouped_columns_load[prefix] = []
         grouped_columns_load[prefix].append(col)
    Ext_Load_joined = pd.DataFrame()
    for prefix, cols in grouped_columns_load.items():
         Ext_Load_joined[f'{prefix}'] =grid.time_series_results['real_load_opf'][cols].sum(axis=1)
    Ext_Load_joined['Total']=grid.time_series_results['real_load_opf'].sum(axis=1)
    
    for col in grid.time_series_results['real_power_opf'].columns:
         if 'RenSource' in col:
            prefix = 'RenSource'  # Group all RenSource together
         else:
            prefix = ''.join(filter(str.isalpha, col))
         if prefix not in grouped_columns:
             grouped_columns[prefix] = []
         grouped_columns[prefix].append(col)
    Ext_Gen_joined = pd.DataFrame()
     # Aggregate columns with the same prefix for external generation
    for prefix, cols in grouped_columns.items():
         Ext_Gen_joined[f'{prefix}'] =grid.time_series_results['real_power_opf'][cols].sum(axis=1)
         
         
    if 'RenSource' in Ext_Gen_joined.columns:
        Ext_Gen_joined  = Ext_Gen_joined[[col for col in Ext_Gen_joined.columns if col != 'RenSource'] + ['RenSource']]
    grid.ts_infeasible_count = infeasible
    grid.time_series_results['real_load_by_zone']  = Ext_Load_joined
    # Track the *model* P_known_AC sign convention aggregated by price zone.
    # In OPF_step_results: opt_P_load = -P_known_AC, so real_load_by_zone is the sign-flipped view.
    grid.time_series_results['real_load_known_by_zone'] = -Ext_Load_joined
    grid.time_series_results['real_power_by_zone'] = Ext_Gen_joined
    grid.time_series_results['reactive_power_opf'].columns = grid.time_series_results['reactive_power_opf'].columns.str.replace('Reactor_' , '',regex=False)
    grid.time_series_results['real_power_opf'].columns = grid.time_series_results['real_power_opf'].columns.str.replace('RenSource_','', regex=False)

def Time_series_statistics(grid, curtail=0.99,over_loading=0.9):

    a = grid.Time_series

    static = []  # Initialize stats as an empty DataFrame

    for ts in a:
            # Calculate statistics for each time series
            mean = np.mean(ts.data)  # Calculate mean
            median = np.median(ts.data)  # Calculate median
            maxim = np.max(ts.data)  # Calculate maximum
            minim = np.min(ts.data)  # Calculate minimum
            mode, count = st.mode(np.round(ts.data, decimals=3))
            iqr = st.iqr(ts.data)

            sorted_data = np.sort(ts.data)
            cumulative_prob = np.linspace(0, 1, len(sorted_data))

            i = find_value_from_cdf(cumulative_prob, curtail)
            name=ts.name
           
            # Create a dictionary to store the statistics
            stats_dict = {
                'Element': name,
                'Mean': mean,
                'Median': median,
                'Maximum': maxim,
                'Minimum': minim,
                'Mode3dec': mode,
                'Mode_count': count,
                'IQR': iqr,
                f'{curtail*100}%': sorted_data[i].item(),
               }

            # Convert the dictionary to a DataFrame and append it to the stats DataFrame
            static.append(stats_dict)

    if grid.Time_series_ran == True:
        # Create a new dictionary with marked DataFrames
        marked_time_series_results = {
            'PF_results': grid.time_series_results['PF_results'].add_suffix('_PF'),
            'ac_loading': grid.time_series_results['ac_loading'].add_suffix('_ACloading'),
            'dc_loading': grid.time_series_results['dc_loading'].add_suffix('_DCloading'),
            'grid_loading': grid.time_series_results['grid_loading'].add_suffix('_gridloading'),
            'ac_MW_to': grid.time_series_results['ac_MW_to'].add_suffix('_ACMWto'),
            'dc_MW_to': grid.time_series_results['dc_MW_to'].add_suffix('_DCMWto'),
            'converter_p_dc': grid.time_series_results['converter_p_dc'].add_suffix('_convP_DC'),
            'converter_q_ac': grid.time_series_results['converter_q_ac'].add_suffix('_convQ_AC'),
            'converter_p_ac': grid.time_series_results['converter_p_ac'].add_suffix('_convP_AC'),
            'real_load_by_zone': grid.time_series_results['real_load_by_zone'].add_suffix('_PL_OPF'),
            'real_load_known_by_zone': grid.time_series_results['real_load_known_by_zone'].add_suffix('_PL_Pknown'),
            'real_power_opf': grid.time_series_results['real_power_opf'].add_suffix('_P_OPF'),
            'reactive_power_opf': grid.time_series_results['reactive_power_opf'].add_suffix('_Q_OPF'),
            'curtailment': grid.time_series_results['curtailment'].add_suffix('_curtail'),
            'converter_loading': grid.time_series_results['converter_loading'].add_suffix('_convloading'),
            'real_power_by_zone': grid.time_series_results['real_power_by_zone'].add_suffix('_zoneP'),
            'prices_by_zone': grid.time_series_results['prices_by_zone'].add_suffix('_price'),
            'PZ_cost_of_generation': grid.time_series_results.get('PZ_cost_of_generation', pd.DataFrame()).add_suffix('_PZcost'),
            'PZ_load': grid.time_series_results.get('PZ_load', pd.DataFrame()).add_suffix('_PZload'),
            'net_price_zone_power': grid.time_series_results['net_price_zone_power'].add_suffix('_netPZ'),
            'a': grid.time_series_results['a'].add_suffix('_a'),
            'b': grid.time_series_results['b'].add_suffix('_b'),
        }
        
        # Merge non-empty DataFrames
        merged_df = pd.concat([df for df in marked_time_series_results.values() if not df.empty], axis=1)
        
        for col in merged_df:
            # Calculate statistics for each column in merged_df
            mean = merged_df[col].mean()  # Calculate mean
            median = merged_df[col].median()  # Calculate median
            maxim = merged_df[col].max()  # Calculate maximum
            minim = merged_df[col].min()  # Calculate minimum
            mode, count = st.mode(merged_df[col].round(3))
            iqr = st.iqr(merged_df[col])

            sorted_data = np.sort(merged_df[col])
            cumulative_prob = np.linspace(0, 1, len(sorted_data))

            i = find_value_from_cdf(cumulative_prob, curtail)
            
            
            if 'loading' in col:
                n = sum(1 for num in merged_df[col] if num > over_loading)
            else:
                n = sum(1 for num in merged_df[col] if num > over_loading*maxim)
                
            # Create a dictionary to store the statistics
            stats_dict = {
                'Element': col,
                'Mean': mean,
                'Median': median,
                'Maximum': maxim,
                'Minimum': minim,
                'Mode3dec': mode,
                'Mode_count': count,
                'IQR': iqr,
                f'{curtail*100}%': sorted_data[i].item(),
               f'Number above {over_loading*100}%': n
            }

            # Convert the dictionary to a DataFrame and append it to the stats DataFrame
            static.append(stats_dict)

    # Reset index of the stats DataFrame
    stats = pd.DataFrame(static)
    stats.set_index('Element', inplace=True)
    grid.Stats = stats

    return stats

def results_TS_OPF(grid,excel_file_path,grid_names=None,stats=None,times=None):
    
    if not excel_file_path.endswith('.xlsx'):
        excel_file_path = f'{excel_file_path}.xlsx'
  
    if grid_names is not None:
        grid.time_series_results['grid_loading'] =grid.time_series_results['grid_loading'].rename(columns=grid_names)


    with pd.ExcelWriter(excel_file_path) as writer:
        # Write each DataFrame to a separate sheet
        if times is not None:
            times_df = pd.DataFrame(list(times.items()), columns=['Metric', 'Time (s)'])
            row_space = pd.DataFrame({'Metric': [''], 'Time (s)': ['']})
            row_infeasible = pd.DataFrame({'Metric': ['Infeasible'], 'Time (s)': [grid.ts_infeasible_count]})
            times_df = pd.concat([times_df, row_space, row_infeasible], ignore_index=True)
            times_df.to_excel(writer, sheet_name='Time', index=False)
        
        (grid.time_series_results['ac_loading']* 100).to_excel(writer, sheet_name='AC line loading', index=True)
        (grid.time_series_results['dc_loading']* 100).to_excel(writer, sheet_name='DC line loading', index=True)
        grid.time_series_results['ac_MW_to'].to_excel(writer, sheet_name='AC MW to', index=True)
        grid.time_series_results['dc_MW_to'].to_excel(writer, sheet_name='DC MW to', index=True)
        (grid.time_series_results['grid_loading']* 100).to_excel(writer, sheet_name='Grid loading', index=True)
    
        (grid.time_series_results['converter_p_dc']*grid.S_base).to_excel(writer, sheet_name='Converter P DC', index=True)
        (grid.time_series_results['converter_q_ac']*grid.S_base).to_excel(writer, sheet_name='Converter Q AC', index=True)
        (grid.time_series_results['converter_p_ac']*grid.S_base).to_excel(writer, sheet_name='Converter P AC', index=True)
        (grid.time_series_results['real_load_by_zone']*grid.S_base).to_excel(writer, sheet_name='Real Load', index=True)
        (grid.time_series_results['real_load_known_by_zone']*grid.S_base).to_excel(writer, sheet_name='Known Load', index=True)
        (grid.time_series_results['real_power_opf']*grid.S_base).to_excel(writer, sheet_name='Real power OPF', index=True)
        (grid.time_series_results['reactive_power_opf']*grid.S_base).to_excel(writer, sheet_name='Reactive OPF', index=True)
        (grid.time_series_results['curtailment']* 100).to_excel(writer, sheet_name='Curtailment', index=True)
    
        (grid.time_series_results['converter_loading']*100).to_excel(writer, sheet_name='Converter loading', index=True)
        (grid.time_series_results['real_power_by_zone']*grid.S_base).to_excel(writer, sheet_name='Real power by zone', index=True)
        grid.time_series_results['net_price_zone_power'].to_excel(writer, sheet_name='Net price zone power', index=True)
        grid.time_series_results['prices_by_zone'].to_excel(writer, sheet_name='Prices by zone', index=True)
        grid.time_series_results['PZ_cost_of_generation'].to_excel(
            writer, sheet_name='PZ cost of generation', index=True
        )
        grid.time_series_results['PZ_load'].to_excel(writer, sheet_name='PZ_load', index=True)
        grid.time_series_results['a'].to_excel(writer, sheet_name='a', index=True)
        grid.time_series_results['b'].to_excel(writer, sheet_name='b', index=True)
        grid.time_series_results['PZ_lb'].to_excel(writer, sheet_name='PZ_lb', index=True)
        grid.time_series_results['PZ_ub'].to_excel(writer, sheet_name='PZ_ub', index=True)
        grid.time_series_results['res_available'].to_excel(writer, sheet_name='res_available', index=True)
        if stats is not None:
            stats.to_excel(writer, sheet_name='stats', index=True)




