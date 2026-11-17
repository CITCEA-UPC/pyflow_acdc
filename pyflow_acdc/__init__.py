# -*- coding: utf-8 -*-
"""
pyflow-acdc package initialization.
Provides grid simulation and power flow analysis functionality.
"""
from pathlib import Path
import importlib.util
import inspect

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
    'Gen_AC',
    'Gen_DC',
    'Storage',
    'Electrolyser',
    'HeatPump',
    'add_gen',
    'add_gen_DC',
    'add_extgrid',
    'add_RenSource',
    'add_storage',
    'add_electrolyser',
    'add_heat_pump',
    'add_generators',

    # Add Zones
    'add_RenSource_zone',
    'add_price_zone',
    'add_MTDC_price_zone',
    'add_offshore_price_zone',

    # Add Time Series
    'add_TimeSeries',
    'time_series_dict',

    #Add investment series
    'add_inv_series',
    'add_gen_mix_limits',

    # Grid Creation and Import
    'create_grid_from_data',
    'create_grid_from_mat',
    'create_grid_from_turbine_graph',
    'extend_grid_from_data',
    'create_grid_from_pickle',
    'change_S_base',

    # Line Modifications
    'change_line_AC_to_expandable',
    'change_line_AC_to_tap_transformer',

    # Expandable / reconductoring setup (always available; not OPF-gated)
    'expand_elements_from_pd',
    'repurpose_element_from_pd',
    'expand_element',
    'update_attributes',
    'base_cost_calculation',

    # Zone Assignments
    'assign_RenToZone',
    'assign_nodeToPrice_Zone',
    'assign_ConvToPrice_Zone',

    # Parameter Calculations
    'cable_parameters',
    'converter_parameters',

    # Utility Functions
    'pol2cart',
    'cart2pol',
    'pol2cartz',
    'cartz2pol',
    'import_orbit_cables',
    'expand_cable_database',
    'current_fuel_type_distribution',
    'initialize_pyflowacdc',
    'create_inv_csv_template',
    'create_gen_limit_csv_template',

    # Power Flow
    'ac_power_flow',
    'dc_power_flow',
    'acdc_sequential',
    'power_flow',

    # Time Series Analysis
    'time_series_pf',
    'ts_acdc_pf',
    'ts_ac_pf',
    'ts_dc_pf',
    'time_series_statistics',
    'update_grid_data',
    'update_grid_for_pf',

    # Export
    'save_grid_to_file',
    'save_grid_to_matlab',
    'save_pickle',
    'export_solver_progress_to_excel',

    # Visualization
    'plot_graph',
    'time_series_prob',
    'plot_neighbour_graph',
    'plot_TS_res',
    'plot_folium',
    'plot_folium_network',
    'save_network_svg',
    'plot_model_feasibility',
    'plot_3D',
    'create_geometries_from_coords',

    # Market Analysis
    'price_zone_data_pd',
    'price_zone_coef_data',
    'plot_curves',
    'clean_entsoe_data',
]

try:
    from .solver_utils import *
    __all__.append('check_available_solvers')
    __all__.append('is_pyomo_solver_available')
except ImportError:
    pass

# Try to import OPF module if pyomo is available
try:
    from .ACDC_OPF import *
    # Time_series module functions that depend on OPF are already imported via Time_series
    # but we need to add them to __all__ only if OPF is available
    __all__.extend([
        'optimal_pf', 'optimal_l_pf', 'pyomo_model_solve', 'opf_obj', 'opf_line_res',
        'opf_price_price_zone', 'translate_pyf_opf',
        'ts_acdc_opf', 'ts_acdc_l_opf', 'results_ts_opf',
    ])
    try:
        from .NL_models.window_opf import (
            window_nl_opf, rolling_window_nl_opf, results_window_opf,
        )
        __all__.extend([
            'window_nl_opf', 'rolling_window_nl_opf', 'results_window_opf',
        ])
    except ImportError:
        pass
    try:
        from .L_models.window_l_opf import window_l_opf, rolling_window_l_opf
        __all__.extend(['window_l_opf', 'rolling_window_l_opf'])
    except ImportError:
        pass
    HAS_OPF = True

    # ACDC_Static_TEP also requires OPF/pyomo
    try:
        from .NL_models.ACDC_Static_TEP import *
        __all__.extend([
            'transmission_expansion',
            'multi_scenario_TEP',
            'export_TEP_multiScenario_results_to_excel',
            'alpha_pareto', 'rate_sensitivity', 'kappa_sensitivity',
            'comprehensive_sensitivity_analysis'
        ])
        try:
            from .NL_models.ACDC_sequential_STEP import *
            __all__.extend(['sequential_STEP', 'sequential_MS_STEP'])
        except ImportError:
            pass
    except ImportError:
        pass

    # Array_OPT depends on both OPF and Static_TEP modules
    try:
        from .Array_OPT import *
        __all__.extend(['wind_farm_CSS', 'sequential_CSS', 'MIP_path_graph', 'simple_assign_cable_types'])
    except ImportError:
        pass

except ImportError:
    HAS_OPF = False

try:
    from .NL_models.ACDC_MultiPeriod_TEP import *
    __all__.extend([
        'multi_period_transmission_expansion',
        'multi_period_MS_TEP',
        'export_and_save_inv_period_svgs',
        'run_opf_for_investment_period',
        'run_ts_opf_for_investment_period',
        'run_opf_for_all_investment_periods',
    ])
except ImportError:
    pass

try:
    from .L_models.ACDC_L_TEP import *
    __all__.extend([
        'linear_transmission_expansion',
        'linear_multi_period_transmission_expansion',
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
        'run_window_dash',
        'run_rolling_dash',
        'run_season_compare_dash',
        'run_mp_ts_dash',
        'create_mp_ts_dash',
        'create_dash_app',
        'create_window_dash_app',
        'create_rolling_dash_app',
        'create_season_compare_dash_app',
        'build_season_window_compare',
        'attach_season_window_compare',
        'resolve_family_df',
        'resolve_season_family_df',
        'available_dash_families',
        'available_family_aggregations',
        'plot_TS_res_from_ts',
        'plot_TS_res_dash',
        'plot_window_res_dash',
        'plot_window_family_dash',
        'plot_season_family_dash',
    ])
    HAS_DASH = True
except ImportError:
    HAS_DASH = False

try:
    from .L_models.AC_L_CSS_ortools import *
    __all__.extend(['optimal_l_css_ortools'])
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
        'cluster_TS', 'run_clustering_analysis', 'run_clustering_analysis_and_plot',
        'identify_correlations', 'cluster_analysis', 'load_precomputed_clusters_to_grid'
    ])
    HAS_CLUSTERING = True
except ImportError:
    HAS_CLUSTERING = False

# SOCP stack — optional; requires [SOCP] extra (cvxpy)
try:
    from .ACDC_convex import (
        apply_ccp_quantiles,
        socp_ccp_optimise,
        socp_ccp_window_optimisation,
        socp_optimise,
        soc_window_optimisation,
        translate_pyf_socp,
    )
    __all__.extend([
        'apply_ccp_quantiles',
        'socp_ccp_optimise',
        'socp_ccp_window_optimisation',
        'socp_optimise',
        'soc_window_optimisation',
        'translate_pyf_socp',
    ])
    HAS_SOCP = True
except ImportError:
    HAS_SOCP = False

# Deprecated mixed-case aliases (snake_case is the default API).
# Imported last so the legacy names resolve to the deprecation wrappers.
from . import depreciation_methods
from .depreciation_methods import *
__all__.extend(depreciation_methods.__all__)

# Dynamically load all .py files in the example_grids folders.
_cases_root = Path(__file__).parent / "example_grids"
_case_folders = [
    _cases_root / "PF",
    _cases_root / "OPF",
    _cases_root / "TEP",
    _cases_root / "Wind_Array",
]


def _pick_case_factory(module, stem):
    candidates = [
        fn
        for _, fn in inspect.getmembers(module, inspect.isfunction)
        if not fn.__name__.startswith("_") and fn.__module__ == module.__name__
    ]
    if not candidates:
        return None
    for fn in candidates:
        if fn.__name__ == stem:
            return fn
    return candidates[0]


# Namespace for primary example-grid factories only.
cases = {}

# Load each .py case module from configured folders
for folder in _case_folders:
    if not folder.exists():
        continue

    for case_file in sorted(folder.glob("*.py")):
        if case_file.name == "__init__.py" or case_file.name.startswith("_"):
            continue

        rel_module = case_file.relative_to(_cases_root).with_suffix("")
        module_name = "__".join(rel_module.parts)
        spec = importlib.util.spec_from_file_location(module_name, case_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Trust boundary: only loads .py from bundled example_grids/

        factory = _pick_case_factory(module, case_file.stem)
        if factory is not None:
            cases[factory.__name__] = factory



