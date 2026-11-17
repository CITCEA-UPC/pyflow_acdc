"""Shared constants for pyflow_tests scripts, doc examples, and runners."""

# --- Moray East plotting ---

MORAY_EAST_CABLE_DECISIONS = {
    "45_46": "MOF_240",
    "43_46": "MOF_240",
    "42_43": "MOF_240",
    "41_42": "MOF_240",
    "40_41": "MOF_630",
    "36_40": "MOF_630",
    "36_100": "MOF_630",
    "38_44": "MOF_240",
    "38_39": "MOF_240",
    "35_39": "MOF_240",
    "33_35": "MOF_240",
    "33_34": "MOF_630",
    "34_100": "MOF_630",
    "27_31": "MOF_240",
    "26_27": "MOF_240",
    "25_26": "MOF_240",
    "24_25": "MOF_240",
    "23_24": "MOF_630",
    "23_32": "MOF_630",
    "32_100": "MOF_630",
    "57_58": "MOF_240",
    "56_57": "MOF_240",
    "55_56": "MOF_240",
    "54_55": "MOF_240",
    "53_54": "MOF_630",
    "37_53": "MOF_630",
    "37_100": "MOF_630",
    "47_67": "MOF_240",
    "47_48": "MOF_240",
    "48_49": "MOF_240",
    "49_50": "MOF_240",
    "50_51": "MOF_630",
    "51_52": "MOF_630",
    "52_100": "MOF_630",
    "70_71": "MOF_240",
    "69_70": "MOF_240",
    "69_73": "MOF_240",
    "72_73": "MOF_240",
    "68_72": "MOF_630",
    "66_68": "MOF_630",
    "62_66": "MOF_630",
    "62_102": "MOF_630",
    "96_99": "MOF_240",
    "95_96": "MOF_240",
    "87_95": "MOF_240",
    "86_87": "MOF_240",
    "63_86": "MOF_630",
    "63_64": "MOF_630",
    "64_65": "MOF_630",
    "65_102": "MOF_630",
    "97_98": "MOF_240",
    "93_97": "MOF_240",
    "93_94": "MOF_240",
    "91_94": "MOF_240",
    "85_91": "MOF_630",
    "78_85": "MOF_630",
    "78_102": "MOF_630",
    "82_88": "MOF_240",
    "88_92": "MOF_240",
    "89_92": "MOF_240",
    "89_90": "MOF_240",
    "77_90": "MOF_630",
    "77_102": "MOF_630",
    "28_29": "MOF_240",
    "29_30": "MOF_240",
    "30_60": "MOF_240",
    "60_102": "MOF_240",
    "83_84": "MOF_240",
    "79_84": "MOF_240",
    "76_79": "MOF_240",
    "61_76": "MOF_240",
    "13_61": "MOF_630",
    "13_16": "MOF_630",
    "16_101": "MOF_630",
    "74_81": "MOF_240",
    "80_81": "MOF_240",
    "75_80": "MOF_240",
    "59_75": "MOF_240",
    "12_59": "MOF_630",
    "11_12": "MOF_630",
    "11_101": "MOF_630",
    "2_3": "MOF_240",
    "1_2": "MOF_240",
    "0_1": "MOF_240",
    "0_6": "MOF_240",
    "5_6": "MOF_630",
    "4_5": "MOF_630",
    "4_101": "MOF_630",
    "14_15": "MOF_240",
    "7_15": "MOF_240",
    "7_8": "MOF_240",
    "8_9": "MOF_240",
    "9_10": "MOF_630",
    "10_101": "MOF_630",
    "21_22": "MOF_240",
    "20_21": "MOF_240",
    "19_20": "MOF_240",
    "18_19": "MOF_240",
    "17_18": "MOF_630",
    "17_101": "MOF_630",
}

CABLE_TYPES_OFF66 = [
    "MOF_240",
    "MOF_300",
    "MOF_630",
    "MOF_800",
]

# --- North Sea grid example data (remote CSVs) ---

from pathlib import Path

NORTH_SEA_GRID_DATA_GITHUB_BASE = (
    "https://raw.githubusercontent.com/CITCEA-UPC/pyflow_acdc/main/examples/North_Sea_grid_data/"
)
NORTH_SEA_GRID_DATA_DIR = Path(__file__).resolve().parents[1] / "examples" / "North_Sea_grid_data"
NORTH_SEA_CLUSTERS_K4_JSON = NORTH_SEA_GRID_DATA_DIR / "clusters_kmeans_medoids_k4.json"
NS_MTDC_MARKET_PRICES_URL = NORTH_SEA_GRID_DATA_GITHUB_BASE + "NS_TS_marketPrices_data_sd2024.csv"
NS_MTDC_WIND_LOAD_URL = NORTH_SEA_GRID_DATA_GITHUB_BASE + "NS_TS_WL_data2024.csv"


def north_sea_ms_clustering_options():
    """Precomputed k=4 clusters for NS 2023+2024 MS TEP (local JSON)."""
    return {
        "n_clusters": 4,
        "precomputed_clusters_path": str(NORTH_SEA_CLUSTERS_K4_JSON),
    }

# --- Case24_MP planning CSVs (remote) ---

CASE24_MP_GITHUB_BASE = (
    "https://raw.githubusercontent.com/CITCEA-UPC/pyflow_acdc/main/examples/Case24_MP/"
)
CASE24_MP_INV_SERIES_URL = CASE24_MP_GITHUB_BASE + "case24_MP_TEP_inv_series_10.csv"
CASE24_MP_GEN_MIX_LIMITS_URL = CASE24_MP_GITHUB_BASE + "case24_MP_TEP_gen_mix_limits.csv"

# --- run_tests.py case lists ---

IGNORED_WARNING_SNIPPETS = [
    "PytestAssertRewriteWarning",
    "Module already imported so cannot be rewritten; dash",
]

DOCS_CASES = [
    "test_docs_index.py",
    "test_docs_usage.py",
    "test_docs_tep.py",
    "test_docs_tep_mp.py",
    "test_docs_csv_import.py",
    "test_docs_modelling_ac.py",
    "test_docs_modelling_dc.py",
    "test_docs_results.py",
    "test_docs_ts.py",
    "test_docs_clustering.py",
    "test_docs_plotting.py",
    "test_docs_tep_pymoo.py",
    "test_docs_wf_array.py",
    "test_docs_dash.py",
    "test_docs_window_opf.py",
    "test_docs_L_models.py",
]

ALL_CASES = [
    *DOCS_CASES,
    "test_example_grids_smoke.py",
    "test_examples_folder_smoke.py",
    "test_model_build_only.py",
    "test_grid_creation.py",
    "test_S_base_change.py",
    "test_grid_mod.py",
    "test_cigreb4_pf.py",
    "test_ts_pf.py",
    "test_save_grid.py",
    "test_DC_OPF.py",
    "test_CigreB4_OPF.py",
    "test_case39ac_OPF.py",
    "test_case39ac_LOPF.py",
    "test_case39acdc_OPF.py",
    "test_case24_3zones_acdc_OPF.py",
    "test_opf_result_helpers.py",
    "test_socp.py",
    "test_matlab_loader.py",
    "test_market_coeff.py",
    "test_solver_utils.py",
    "test_pyomo_model_solve.py",
    "test_solver_progress_plot_export.py",
    "test_graph_dash.py",
    "test_folium.py",
    "test_plot.py",
    "test_case24_OPF.py",
    "test_case6_TEP_DC.py",
    "test_array_sizing.py",
    "test_sequential_array.py",
    "test_sequential_array_ortools.py",
    "test_unified_array_pyomo.py",
    "test_unified_array_ortools.py",
]

ARRAY_CASES = [
    "test_array_sizing.py",
    "test_sequential_array.py",
    "test_sequential_array_ortools.py",
    "test_unified_array_pyomo.py",
    "test_unified_array_ortools.py",
]

OPF_CASES = [
    "test_DC_OPF.py",
    "test_CigreB4_OPF.py",
    "test_case39ac_OPF.py",
    "test_case39acdc_OPF.py",
    "test_case24_3zones_acdc_OPF.py",
    "test_opf_result_helpers.py",
]

QUICK_CASES = [
    "test_docs_index.py",
    "test_docs_usage.py",
    "test_docs_modelling_ac.py",
    "test_docs_modelling_dc.py",
    "test_docs_csv_import.py",
    "test_grid_creation.py",
    "test_S_base_change.py",
    "test_grid_mod.py",
    "test_cigreb4_pf.py",
    "test_ts_pf.py",
    "test_save_grid.py",
    "test_matlab_loader.py",
    "test_example_grids_smoke.py",
    "test_model_build_only.py",
    "test_plot.py",
    "test_OPF_quick_runner.py",
    "test_solver_utils.py",
    "test_pyomo_model_solve.py",
    "test_solver_progress_plot_export.py",
    "test_graph_dash.py",
]

TEP_CASES = [
    "test_case24_OPF.py",
    "test_case6_TEP_DC.py",
    *ARRAY_CASES,
]

# --- test_OPF_quick_runner.py ---

FULL_OPF_TEP_CASE_MODULES = [
    "pyflow_tests.test_DC_OPF",
    "pyflow_tests.test_CigreB4_OPF",
    "pyflow_tests.test_case39ac_OPF",
    "pyflow_tests.test_case39acdc_OPF",
    "pyflow_tests.test_case24_3zones_acdc_OPF",
    "pyflow_tests.test_opf_result_helpers",
    "pyflow_tests.test_case24_OPF",
    "pyflow_tests.test_case39ac_LOPF",
    "pyflow_tests.test_case6_TEP_DC",
    "pyflow_tests.test_array_sizing",
]
