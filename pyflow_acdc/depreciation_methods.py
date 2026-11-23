"""Deprecated mixed-case aliases for the snake_case public API.

snake_case is the default naming for the public API. This module is the single
place that keeps the legacy mixed-case / PascalCase names working: each old
name forwards to its new snake_case implementation and emits a
``DeprecationWarning``.

New code should import the snake_case names directly from ``pyflow_acdc``
(e.g. ``pyf.power_flow`` instead of ``pyf.Power_flow``).

Aliases for optional features (OPF, array cable-string sizing) are only created
when their backing module imports successfully, mirroring the optional-
dependency guards in ``__init__``.
"""
import functools
import warnings

__all__ = []


def _deprecated(new_func, old_name):
    """Return a wrapper named ``old_name`` that warns and calls ``new_func``."""
    new_name = new_func.__name__

    @functools.wraps(new_func)
    def _wrapper(*args, **kwargs):
        warnings.warn(
            f"'{old_name}' is deprecated and will be removed in a future "
            f"release; use '{new_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return new_func(*args, **kwargs)

    _wrapper.__name__ = old_name
    _wrapper.__qualname__ = old_name
    _wrapper.__doc__ = f"Deprecated alias for ``{new_name}``. Use ``{new_name}`` instead."
    return _wrapper


def _register(new_func, old_name):
    globals()[old_name] = _deprecated(new_func, old_name)
    __all__.append(old_name)


def _register_method(cls, old_name, new_name):
    """Attach a deprecated method ``old_name`` on ``cls`` forwarding to ``new_name``."""
    new_method = getattr(cls, new_name)

    @functools.wraps(new_method)
    def _wrapper(self, *args, **kwargs):
        warnings.warn(
            f"'{cls.__name__}.{old_name}' is deprecated and will be removed in a "
            f"future release; use '{cls.__name__}.{new_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, new_name)(*args, **kwargs)

    _wrapper.__name__ = old_name
    _wrapper.__qualname__ = f"{cls.__name__}.{old_name}"
    _wrapper.__doc__ = f"Deprecated alias for ``{new_name}``. Use ``{new_name}`` instead."
    setattr(cls, old_name, _wrapper)


# --- Always-available (core) aliases -------------------------------------
from .ACDC_PF import ac_power_flow, acdc_sequential, dc_power_flow, power_flow
from .Graph_and_plot import plot_graph, time_series_prob
from .grid_analysis import cable_parameters, converter_parameters
from .grid_creator import (
    create_grid_from_data,
    create_grid_from_mat,
    create_grid_from_pickle,
    create_grid_from_turbine_graph,
    extend_grid_from_data,
)
from .Time_series import time_series_pf, time_series_statistics, ts_acdc_pf

_register(power_flow, 'Power_flow')
_register(ac_power_flow, 'AC_PowerFlow')
_register(dc_power_flow, 'DC_PowerFlow')
_register(acdc_sequential, 'ACDC_sequential')
_register(create_grid_from_data, 'Create_grid_from_data')
_register(create_grid_from_mat, 'Create_grid_from_mat')
_register(create_grid_from_turbine_graph, 'Create_grid_from_turbine_graph')
_register(extend_grid_from_data, 'Extend_grid_from_data')
_register(create_grid_from_pickle, 'Create_grid_from_pickle')
_register(cable_parameters, 'Cable_parameters')
_register(converter_parameters, 'Converter_parameters')
_register(time_series_pf, 'Time_series_PF')
_register(ts_acdc_pf, 'TS_ACDC_PF')
_register(time_series_statistics, 'Time_series_statistics')
_register(plot_graph, 'plot_Graph')
_register(time_series_prob, 'Time_series_prob')

# --- Results class methods (snake_case is canonical) ----------------------
from .Results_class import Results

_RESULTS_METHOD_ALIASES = {
    'All': 'all',
    'All_AC': 'all_ac',
    'All_DC': 'all_dc',
    'Slack_All': 'slack_all',
    'Slack_AC': 'slack_ac',
    'Slack_DC': 'slack_dc',
    'Power_loss': 'power_loss',
    'Power_loss_AC': 'power_loss_ac',
    'Power_loss_DC': 'power_loss_dc',
    'DC_bus': 'dc_bus',
    'AC_Powerflow': 'ac_powerflow',
    'AC_voltage': 'ac_voltage',
    'AC_lines_current': 'ac_lines_current',
    'AC_exp_lines_power': 'ac_exp_lines_power',
    'AC_lines_power': 'ac_lines_power',
    'Ext_gen': 'ext_gen',
    'Ext_REN': 'ext_ren',
    'Clustering_results': 'clustering_results',
    'Cluster_representatives': 'cluster_representatives',
    'Clustering_technique': 'clustering_technique',
    'Clustering_Time_series_statistics': 'clustering_time_series_statistics',
    'TEP_multiScenario_res': 'tep_multi_scenario_res',
    'TEP_N': 'tep_n',
    'TEP_norm': 'tep_norm',
    'OBJ_res': 'obj_res',
    'TEP_TS_norm': 'tep_ts_norm',
    'MP_TEP_results': 'mp_tep_results',
    'MP_MS_TEP_results': 'mp_ms_tep_results',
    'MP_TEP_obj_res': 'mp_tep_obj_res',
    'MP_MS_TEP_obj_res': 'mp_ms_tep_obj_res',
    'MP_TEP_fuel_type_distribution': 'mp_tep_fuel_type_distribution',
    'Seq_STEP_results': 'seq_step_results',
    'Seq_STEP_obj_res': 'seq_step_obj_res',
    'Seq_STEP_fuel_type_distribution': 'seq_step_fuel_type_distribution',
    'Seq_MS_STEP_results': 'seq_ms_step_results',
    'Seq_MS_STEP_obj_res': 'seq_ms_step_obj_res',
    'Seq_MS_STEP_fuel_type_distribution': 'seq_ms_step_fuel_type_distribution',
    'Price_Zone': 'price_zone',
    'DC_lines_current': 'dc_lines_current',
    'DC_lines_power': 'dc_lines_power',
    'DC_converter': 'dc_converter',
    'Converter': 'converter',
}
for _old, _new in _RESULTS_METHOD_ALIASES.items():
    _register_method(Results, _old, _new)

# --- Grid class methods (snake_case is canonical) -------------------------
from .Classes import Grid

_GRID_METHOD_ALIASES = {
    'Update_Graph_AC': 'update_graph_ac',
    'Update_Graph_DC': 'update_graph_dc',
    'Update_PQ_AC': 'update_pq_ac',
    'Update_P_DC': 'update_p_dc',
    'Line_AC_calc': 'line_ac_calc',
    'Line_AC_calc_exp': 'line_ac_calc_exp',
    'Line_DC_calc': 'line_dc_calc',
    'Check_SlacknDroop': 'check_slack_n_droop',
}
for _old, _new in _GRID_METHOD_ALIASES.items():
    _register_method(Grid, _old, _new)

# --- OPF (requires pyomo) -------------------------------------------------
try:
    from .ACDC_OPF import (
        opf_line_res,
        opf_obj,
        opf_price_price_zone,
        optimal_l_pf,
        optimal_pf,
        translate_pyf_opf,
    )
    _register(optimal_pf, 'Optimal_PF')
    _register(optimal_l_pf, 'Optimal_L_PF')
    _register(opf_obj, 'OPF_obj')
    _register(opf_line_res, 'OPF_line_res')
    _register(opf_price_price_zone, 'OPF_price_priceZone')
    _register(translate_pyf_opf, 'Translate_pyf_OPF')
except ImportError:
    pass

# --- Expandable setup (always available; not OPF-gated) -------------------
try:
    from .grid_modifications import expand_element
    _register(expand_element, 'Expand_element')
except ImportError:
    pass

# --- Static TEP (requires pyomo) ------------------------------------------
try:
    from .NL_models.ACDC_Static_TEP import (
        export_TEP_multiScenario_results_to_excel,
    )
    _register(export_TEP_multiScenario_results_to_excel, 'export_TEP_TS_results_to_excel')
except ImportError:
    pass

try:
    from .Time_series import results_ts_opf, ts_acdc_opf
    _register(ts_acdc_opf, 'TS_ACDC_OPF')
    _register(results_ts_opf, 'results_TS_OPF')
except ImportError:
    pass

# --- Array cable-string sizing backends -----------------------------------
try:
    from .L_models.AC_L_CSS_ortools import optimal_l_css_ortools
    _register(optimal_l_css_ortools, 'Optimal_L_CSS_ortools')
except ImportError:
    pass
