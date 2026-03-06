# generate_grids.py - Run ONCE to create pickle files in parks_torque/
# Two grids per case: {case}_gebco.pkl.gz and {case}_flat.pkl.gz
# Then benchmark scripts load via pyf.Create_grid_from_pickle()
from clean_main import create_array_graph_from_geojson
import pyflow_acdc as pyf
import os
import time
import json

path = os.path.dirname(os.path.abspath(__file__))
username = (os.getenv('USERNAME') or os.getenv('USER')
            or os.path.expanduser('~').split(os.sep)[-1])
remote = username.lower() == 'bcv'
case_folder = "parks_clean"
data_path_0 = "Users/BernardoCastro/Documents/Youwind/youwind/"
if remote:
    data_path_0 = "Users/bcv/"
data_path = "C:/" + data_path_0

cases = {
    #'albatros':         {'T_MW':9.5,'T_kV':33,'loc':'offshore','sub_k':20,'rotor_diameter':154},
    #'alpha_ventus':     {'T_MW':5.0,'T_kV':66,'loc':'offshore','sub_k':20,'rotor_diameter':126},
    'Anholt':           {'T_MW':3.6,'T_kV':33,'loc':'offshore','sub_k':60,'rotor_diameter':120},
    #'arcadis_ost':      {'T_MW':9.5,'T_kV':66,'loc':'offshore','sub_k':20,'rotor_diameter':174},
    #'Baltic_eagle':     {'T_MW':9.5,'T_kV':66,'loc':'offshore','sub_k':20,'rotor_diameter':174},
    'Barrow':           {'T_MW':3,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':90},
    #'Beatrice':         {'T_MW':7.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':154},
    #'DanTysk':          {'T_MW':3.6,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':120},
    #'Fryslaan':         {'T_MW':4.3,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':130},
    #'Global_Tech_I':    {'T_MW':5.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':116},
    #'HornSeaOne':       {'T_MW':7.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':154},
    #'HornSeaTwo':       {'T_MW':8.0,'T_kV':66,'loc':'offshore','sub_k':40,'rotor_diameter':167},
    #'HornsRev1':        {'T_MW':2.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':80},
    #'HornsRev2':        {'T_MW':2.3,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':93},
    #'HornsRev3':        {'T_MW':8.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':164},
    #'Kaskasi':          {'T_MW':8.0,'T_kV':66,'loc':'offshore','sub_k':40,'rotor_diameter':167},
    #'Kentish':          {'T_MW':3.0,'T_kV':33,'loc':'offshore','sub_k':20,'rotor_diameter':90},
    #'Meerwind_Sud_Ost': {'T_MW':3.6,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':120},
    #'Moray_East':       {'T_MW':9.5,'T_kV':66,'loc':'offshore','sub_k':40,'rotor_diameter':164},
    #'Moray_West':       {'T_MW':14,'T_kV':66,'loc':'offshore','sub_k':40,'rotor_diameter':222},
    #'Nordsee_one':      {'T_MW':6.2,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':126},
    'Nordsee_ost':      {'T_MW':6.2,'T_kV':66,'loc':'offshore','sub_k':20,'rotor_diameter':126},
    #'Princess_amalia':  {'T_MW':2.0,'T_kV':22,'loc':'offshore','sub_k':40,'rotor_diameter':80},
    #'seagreen':         {'T_MW':10.0,'T_kV':66,'loc':'offshore','sub_k':50,'rotor_diameter':164},
    #'Thanet':           {'T_MW':3,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':100},
    #'Triton_Knoll':     {'T_MW':9.5,'T_kV':66,'loc':'offshore','sub_k':40,'rotor_diameter':164},
    #'WestofDuddon':     {'T_MW':3.6,'T_kV':33,'loc':'offshore','sub_k':80,'rotor_diameter':120},
    'Westermost_Rough': {'T_MW':6.0,'T_kV':33,'loc':'offshore','sub_k':40,'rotor_diameter':154},
    #'Bhlaraidh':        {'T_MW':3.45,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':117},
    #'Bronco_Plains':    {'T_MW':2.8,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':127},
    #'Coromuel':         {'T_MW':2.8,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':127},
    #'Griffin':          {'T_MW':2.3,'T_kV':33,'loc':'onshore','sub_k':60,'rotor_diameter':101},
    #'Serra_Voltorera':  {'T_MW':1.67,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':74},
    #'Storheia_vindpark':{'T_MW':3.6,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':117},
    #'Stronelairg':      {'T_MW':3.45,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':117},
    #'Trucafort_one':    {'T_MW':0.225,'T_kV':33,'loc':'onshore','sub_k':20,'rotor_diameter':28},
    #'Trucafort_two':    {'T_MW':0.6,'T_kV':33,'loc':'onshore','sub_k':40,'rotor_diameter':44}
}

# Cable type definitions
_sizes_onshore = [95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000, 1200, 1400, 1600, 2000]
_sizes_offshore_22 = [95, 120, 150, 185, 240, 300, 400, 500, 630]
_sizes_offshore_33 = [95, 120, 150, 185, 240, 300, 400, 500, 630, 800]
_sizes_offshore_66 = [95, 120, 150, 185, 240, 300, 400, 500, 630, 800, 1000]

cable_types_on33 = [
    f'ABB_extrapolated_XLPE_Cu_33kV_ground_trefoil_{size}mm2' for size in _sizes_onshore
]
    
cable_types_on66 = [
    f'ABB_XLPE_Cu_66kV_ground_trefoil_{size}mm2' for size in _sizes_onshore
]

cable_types_off22 = [
    f'ABB_XLPE_Cu_20kV_sub_{size}mm2' for size in _sizes_offshore_22
]

cable_types_off33 = [
    f'ABB_XLPE_Cu_33kV_sub_{size}mm2' for size in _sizes_offshore_33
]

cable_types_off66 = [
    f'ABB_XLPE_Cu_66kV_sub_{size}mm2' for size in _sizes_offshore_66
]

cable_types_off66_moray_west = [
    f'ABB_XLPE_Al_66kV_sub_{size}mm2' for size in _sizes_offshore_66
]

nt = 2
ct = 3
LCoE = 91


def get_cable_types(kV):
    if cases[case]['loc'] == 'offshore':            
        if kV == 66:
            return cable_types_off66
        elif kV >= 30:
            return cable_types_off33
        return cable_types_off22
    else:
        if kV <= 33:
            return cable_types_on33 
        return cable_types_on66


def create_graph(case, data_source):
    rd = cases[case]['rotor_diameter']
    gj = os.path.join(path, case_folder, case + '.geojson')
    if not os.path.exists(gj):
        print('  GeoJSON not found, skipping: %s' % gj)
        return None, None
    ag, Data, _fig = create_array_graph_from_geojson(
        gj, n_subdiv=10, dense_connection_radius=None,
        turbine_k_neighbors=None, turbine_protection_radius=rd / 2,
        substation_k_neighbors=None, inclination_threshold=10,
        crossing_method='merged', simplify_tolerance=0.00001,
        data_path=data_path, data_source=data_source,
        delunay_densification=True, final_fig=False,
        print_json=False, plot=False, verbose=False)
    return ag, Data


def build_grid(case, array_graph, Data):
    mw = cases[case]['T_MW']
    kV = cases[case]['T_kV']
    ctypes = get_cable_types(kV)

    if "turbine" in Data and hasattr(Data["turbine"], "assign"):
        Data["turbine"]["MW_rating"] = mw
        Data["turbine"]["kV_rating"] = kV
        Data["turbine"]["connections"] = nt

    sk = 'offshore_substation' if 'offshore_substation' in Data else 'transformer_station'
    if sk in Data and hasattr(Data[sk], "assign"):
        Data[sk]["kV_rating"] = kV
        Data[sk]["connections"] = None

    grid, _ = pyf.Create_grid_from_turbine_graph(
        array_graph, Data, cable_types=ctypes,
        cable_types_allowed=ct, curtailment_allowed=0,
        LCoE=LCoE, name=case)
    return grid


if __name__ == '__main__':
    out = os.path.join(path, case_folder)
    os.makedirs(out, exist_ok=True)
    meta = {}

    for case in cases:
        print()
        print('=' * 60)
        print('  ' + case)
        print('=' * 60)
        mw = cases[case]['T_MW']
        kV = cases[case]['T_kV']

        for tag, ds in [('gebco', 'gebco'), ('flat', None)]:
            print('  [%s] graph ...' % tag)
            t0 = time.perf_counter()
            ag, Data = create_graph(case, data_source=ds)
            if ag is None or Data is None:
                continue
            gt = time.perf_counter() - t0
            print('  [%s] graph done in %.1fs -> building grid ...' % (tag, gt))
            grid = build_grid(case, ag, Data)

            fp = os.path.join(out, case + '_' + tag + '.pkl.gz')
            pyf.save_pickle(grid, fp)
            kb = os.path.getsize(fp) / 1024
            print('  [%s] saved %s  (%.0f KB)' % (tag, fp, kb))

            sk = 'offshore_substation' if 'offshore_substation' in Data else 'transformer_station'
            nT = len(Data['turbine'])
            nS = len(Data[sk])
            nE = ag.number_of_edges()
            nX = len(Data.get('crossing_pairs', []))

            mf = None
            try:
                cable_opt = grid.Cable_options[0]
                ratings = getattr(cable_opt, 'MVA_ratings', None)
                if ratings:
                    mf = max(1, int(max(ratings) / mw))
            except Exception:
                pass
            if mf is None:
                if kV == 66:
                    mf = int(94.31 / mw)
                elif kV >= 30:
                    mf = int(44.30 / mw)
                else:
                    mf = int(24.77 / mw)

            if tag == 'gebco':
                meta[case] = {
                    'T_MW': mw, 'T_kV': kV,
                    'n_turbines': nT, 'n_substations': nS,
                    'n_edges': nE, 'n_crossings': nX,
                    'max_flow': mf,
                    'graph_time_gebco': round(gt, 2),
                }
            else:
                meta[case]['graph_time_flat'] = round(gt, 2)

    mp = os.path.join(out, 'grid_metadata.json')
    with open(mp, 'w') as f:
        json.dump(meta, f, indent=2)
    print('\nMetadata -> ' + mp)
    print('Done!')
