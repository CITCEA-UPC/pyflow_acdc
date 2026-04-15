# -*- coding: utf-8 -*-
"""
PyFlow-ACDC initialization module.
Provides grid simulation and power flow analysis functionality.
"""
from pathlib import Path
import importlib.util

# Core imports - required modules
from .Results_class import *
from .grid_modifications import *
from .grid_analysis import *
from .grid_creator import *
from .Classes import *
from .Export_files import *
from .Time_series import *
from .ACDC_PF import *
from .Graph_and_plot import *
from .Market_Coeff import *

# Define what should be available when users do: from pyflow_acdc import *
__all__ = [
    # Results
    'Results',
    # Grid
    'Grid', 
    'Node_AC',
    'Node_DC',
    'Line_AC',
    'Line_DC',
    'AC_DC_converter',

    # Add Grid Elements
    'add_AC_node',
    'add_DC_node',
    'add_line_AC',
    'add_line_DC',
    'add_ACDC_converter',
    'add_DCDC_converter',
    'add_gen',
    'add_gen_DC',
    'add_extgrid',
    'add_RenSource',
    'add_generators',
    
    # Add Zones
    'add_RenSource_zone',
    'add_price_zone',
    'add_MTDC_price_zone',
    'add_offshore_price_zone',
    
    # Add Time Series
    'add_TimeSeries',
    
    #Add investment series
    'add_inv_series',
    'add_gen_mix_limits',
    
    # Grid Creation and Import
    'Create_grid_from_data',
    'Create_grid_from_mat',
    'Create_grid_from_turbine_graph',
    'Extend_grid_from_data',
    'Create_grid_from_pickle',
    
    # Line Modifications
    'change_line_AC_to_expandable',
    'change_line_AC_to_tap_transformer',
    
    # Zone Assignments
    'assign_RenToZone',
    'assign_nodeToPrice_Zone',
    'assign_ConvToPrice_Zone',
    
    # Parameter Calculations
    'Cable_parameters',
    'Converter_parameters',
    
    # Utility Functions
    'pol2cart',
    'cart2pol',
    'pol2cartz',
    'cartz2pol',
    'import_orbit_cables',
    'current_fuel_type_distribution',
    'initialize_pyflowacdc',
    'create_inv_csv_template',
    'create_gen_limit_csv_template',
    
    # Power Flow
    'AC_PowerFlow',
    'DC_PowerFlow',
    'ACDC_sequential',
    'Power_flow',
    
    # Time Series Analysis
    'Time_series_PF',
    'TS_ACDC_PF',
    'Time_series_statistics',
    'update_grid_data',
    
    # Export
    'save_grid_to_file',
    'save_grid_to_matlab',
    'save_pickle',
    'export_solver_progress_to_excel',

    # Visualization
    'plot_Graph',
    'Time_series_prob',
    'plot_neighbour_graph',
    'plot_TS_res',
    'plot_folium',
    'plot_folium_network',
    'save_network_svg',
    'plot_model_feasibility',
    'plot_3D',
    
    # Market Analysis
    'price_zone_data_pd',
    'price_zone_coef_data',
    'plot_curves',
    'clean_entsoe_data',
]

# Try to import OPF module if pyomo is available
try:
    from .ACDC_OPF import *
    # Time_series module functions that depend on OPF are already imported via Time_series
    # but we need to add them to __all__ only if OPF is available
    __all__.extend([
        'Optimal_PF', 'Optimal_L_PF', 'pyomo_model_solve', 'OPF_obj', 'OPF_line_res',
        'OPF_price_priceZone', 'Translate_pyf_OPF',
        'TS_ACDC_OPF', 'results_TS_OPF'
    ])
    HAS_OPF = True
    
    # ACDC_Static_TEP also requires OPF/pyomo
    try:
        from .ACDC_Static_TEP import *
        __all__.extend([
            'transmission_expansion', 'linear_transmission_expansion',
            'multi_scenario_TEP', 'expand_elements_from_pd',
            'repurpose_element_from_pd', 'update_attributes', 'Expand_element',
            'Translate_pd_TEP', 'export_TEP_TS_results_to_excel',
            'alpha_pareto', 'rate_sensitivity', 'kappa_sensitivity',
            'comprehensive_sensitivity_analysis'
        ])
        try:
            from .ACDC_sequential_STEP import *
            __all__.extend(['sequential_STEP', 'sequential_MS_STEP'])
        except ImportError:
            pass
    except ImportError:
        pass
    
    # Array_OPT depends on both OPF and Static_TEP modules
    try:
        from .Array_OPT import *
        __all__.extend(['simple_CSS', 'sequential_CSS', 'MIP_path_graph', 'simple_assign_cable_types'])
    except ImportError:
        pass
    
except ImportError:
    HAS_OPF = False

try:
    from .ACDC_MultiPeriod_TEP import *
    __all__.extend([
        'multi_period_transmission_expansion',
        'multi_period_MS_TEP',
        'export_and_save_inv_period_svgs',
        'run_opf_for_investment_period',
        'run_ts_opf_for_investment_period',
    ])
except ImportError:
    pass
    
try:
    from .ACDC_TEP_pymoo import *
    __all__.append('transmission_expansion_pymoo')
    HAS_TEP_PYMOO = True
except ImportError:
    HAS_TEP_PYMOO = False

try:
    from .Graph_Dash import *
    __all__.extend([
        'run_dash',
        'run_ts_dash',
        'run_mp_ts_dash',
        'create_mp_ts_dash',
        'plot_TS_res_from_ts',
    ])
    HAS_DASH = True
except ImportError:
    HAS_DASH = False
    
try:
    from .AC_L_CSS_gurobi import *
    __all__.extend(['Optimal_L_CSS_gurobi'])
    HAS_AC_L_CSS_GUROBI = True
except ImportError:
    HAS_AC_L_CSS_GUROBI = False

try:
    from .AC_L_CSS_ortools import *
    __all__.extend(['Optimal_L_CSS_ortools'])
    HAS_AC_L_CSS_ORTOOLS = True
except ImportError:
    HAS_AC_L_CSS_ORTOOLS = False

try:
    from .Mapping import *
    HAS_MAPPING = True
except ImportError:
    HAS_MAPPING = False

try:
    from .Time_series_clustering import *
    __all__.extend([
        'cluster_TS', 'run_clustering_analysis_and_plot',
        'identify_correlations', 'cluster_analysis', 'load_precomputed_clusters_to_grid'
    ])
    HAS_CLUSTERING = True
except ImportError:
    HAS_CLUSTERING = False

# Dynamically load all .py files in the example_grids folders.
_cases_root = Path(__file__).parent / "example_grids"
_case_folders = [
    _cases_root,
    _cases_root / "PF",
    _cases_root / "OPF",
    _cases_root / "TEP",
    _cases_root / "Wind_Array",
]

# Namespace for all loaded cases
cases = {}

# Load each .py case module from configured folders
for folder in _case_folders:
    if not folder.exists():
        continue

    for case_file in sorted(folder.glob("*.py")):
        if case_file.name == "__init__.py":
            continue

        rel_module = case_file.relative_to(_cases_root).with_suffix("")
        module_name = "__".join(rel_module.parts)
        spec = importlib.util.spec_from_file_location(module_name, case_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Trust boundary: only loads .py from bundled example_grids/
        
        # Add all public functions from the module to the `cases` namespace
        cases.update({name: obj for name, obj in vars(module).items() if not name.startswith("_")})

    

