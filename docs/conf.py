# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

# Make the package importable for autodoc when building from a source checkout
# (Read the Docs installs it via `pip install .`, but local builds may not).
sys.path.insert(0, os.path.abspath(".."))
sys.path.insert(0, os.path.abspath("_extensions"))


# -- Project information -----------------------------------------------------

project = 'pyflow-acdc'
copyright = '2025-2026, Bernardo Castro Valerio'
author = 'Bernardo Castro Valerio'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'myst_parser',
    'themed_figure',
]

# Optional/heavy dependencies are not installed in the docs build environment
# (Read the Docs only installs the core deps via `pip install .`). The package
# guards them with try/except ImportError, but autodoc still needs to import the
# submodules to read signatures/docstrings, so we mock these imports.
autodoc_mock_imports = [
    "pyomo",
    "cvxpy",
    "dash",
    "ortools",
    "pymoo",
    "gurobipy",
    "folium",
    "branca",
    "kaleido",
    "highspy",
]

# Keep rendered names short (e.g. ``power_flow`` instead of
# ``pyflow_acdc.power_flow``) and preserve source order of members.
add_module_names = False
autodoc_member_order = "bysource"
autodoc_typehints = "description"
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# Theme-aware figures: RST id -> paths under docs/images/<folder>/.
# Default: ``{name}.svg`` in both themes. ``dual_theme``: separate light/dark pair.
_F = "modelling"
_F_ICONS = "modelling/icons"
_F_CASES = "cases"
_F_PLOTTING = "plotting"
_F_EXAMPLES = "examples"
_F_LOGOS = "logos"


def _themed_figure(
    name: str,
    folder: str,
    *,
    dual_theme: bool = False,
) -> dict[str, str]:
    """Register a themed figure under ``docs/images/<folder>/``.

    Default: ``{name}.svg`` in both light and dark themes.
    ``dual_theme``: ``{name}.svg`` (light) and ``{name}_dark.svg`` (dark).
    """
    rel = f"{folder}/{name}"
    light = f"{rel}.svg"
    if dual_theme:
        return {
            "folder": folder,
            "dark": f"{rel}_dark.svg",
            "light": light,
        }
    return {"folder": folder, "dark": light, "light": light}


themed_figure_map = {
    "pyflowacdc_logo": _themed_figure("logo", _F_LOGOS, dual_theme=True),
    "stagg5": _themed_figure("Stagg5MATACDC", _F_CASES, dual_theme=True),
    # System modelling — diagrams (light + dark variants)
    "ac_node_model": _themed_figure("AC_node_model", _F, dual_theme=True),
    "ac_line_pi": _themed_figure("AC_line_pi", _F, dual_theme=True),
    "ac_ybusbranch": _themed_figure("AC_ybusbranch", _F, dual_theme=True),
    "ac_reconducting": _themed_figure("AC_reconducting", _F, dual_theme=True),
    "ac_array": _themed_figure("AC_array", _F, dual_theme=True),
    "dc_node_model": _themed_figure("DC_node_model", _F, dual_theme=True),
    "dc_line": _themed_figure("DC_line", _F, dual_theme=True),
    "dc_expbranch": _themed_figure("DC_expbranch", _F, dual_theme=True),
    "dcdc_conv": _themed_figure("DCDC_conv", _F, dual_theme=True),
    "assymetrical": _themed_figure("assymetrical", _F, dual_theme=True),
    "symetrical": _themed_figure("symetrical", _F, dual_theme=True),
    "bipolar_exp": _themed_figure("bipolar_exp", _F, dual_theme=True),
    "converter_model": _themed_figure("Converter_model", _F, dual_theme=True),
    "ren_sources_model": _themed_figure("Ren_sources_model", _F, dual_theme=True),
    "gen_model": _themed_figure("Gen_model", _F, dual_theme=True),
    "ren_source_limits": _themed_figure("RenGen_limits", _F, dual_theme=True),
    "gen_limits": _themed_figure("Gen_limits", _F, dual_theme=True),
    "prize_zone_model": _themed_figure("prize_zone_model", _F, dual_theme=True),
    # Generation-type icons
    "wind": _themed_figure("wind", _F_ICONS),
    "offshore_wind": _themed_figure("offshore_wind", _F_ICONS),
    "onshore_wind": _themed_figure("onshore_wind", _F_ICONS),
    "solar": _themed_figure("solar", _F_ICONS),
    "hydro": _themed_figure("hydro", _F_ICONS),
    "nuclear": _themed_figure("nuclear", _F_ICONS),
    "coal": _themed_figure("coal", _F_ICONS),
    "solid_biomass": _themed_figure("Solid_Biomass", _F_ICONS),
    "geothermal": _themed_figure("Geothermal", _F_ICONS),
    "lignite": _themed_figure("Lignite", _F_ICONS),
    "natural_gas": _themed_figure("Natural_Gas", _F_ICONS),
    "oil": _themed_figure("Oil", _F_ICONS),
    "waste": _themed_figure("Waste", _F_ICONS),
    "biogas": _themed_figure("Biogas", _F_ICONS),
    "ccgt": _themed_figure("CCGT", _F_ICONS),
    "diesel": _themed_figure("diesel", _F_ICONS),
    "reactor": _themed_figure("reactor", _F_ICONS),
    "gen": _themed_figure("gen", _F_ICONS),
    # Power flow
    "sequential_mod": _themed_figure("Sequential_mod", _F_EXAMPLES),
    # Plotting
    "ts_plot_browser": _themed_figure("ts_plot_browser", _F_PLOTTING),
    "ts_plot_save": _themed_figure("ts_plot_save", _F_PLOTTING),
    "owpp_be_distribution": _themed_figure("OWPP_BE_distribution", _F_PLOTTING),
    "be_price_distribution": _themed_figure("BE_price_distribution", _F_PLOTTING),
    "l_be_distribution": _themed_figure("L_BE_distribution", _F_PLOTTING),
    "case24acdc_full": _themed_figure("case24acdc_full", _F_CASES),
    "case24acdc_neig": _themed_figure("case24acdc_neig", _F_CASES),
    "grid_network": _themed_figure("grid_network", _F_PLOTTING),
    "3d_plot": _themed_figure("3d_plot", _F_PLOTTING),
    # UI screenshots
    "dash_example": _themed_figure("dash_example", _F_EXAMPLES),
    "pei_season_compare_dash": {
        "folder": _F_EXAMPLES,
        "dark": f"{_F_EXAMPLES}/pei_season_compare_dash.png",
        "light": f"{_F_EXAMPLES}/pei_season_compare_dash.png",
    },
    "north_sea_folium": _themed_figure("north_sea_folium", _F_EXAMPLES),
}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'
html_title = project

# Custom CSS to override background color
html_css_files = ['custom.css']

# Remove or comment out the general html_logo setting
# html_logo = '_static/logo.svg'

# Theme options
html_theme_options = {
    "light_css_variables": {
        "color-foreground-primary": "#172033",
        "color-foreground-secondary": "#3f4f63",
        "color-foreground-muted": "#6b7788",
        "color-foreground-border": "#c7d0dc",

        "color-background-primary": "#f7f9fc",
        "color-background-secondary": "#eef3f8",
        "color-background-hover": "#e1e8f0",
        "color-background-border": "#d6dee8",

        "color-brand-primary": "#2563eb",
        "color-brand-content": "#1d4ed8",
        "color-brand-visited": "#6d28d9",

        "color-sidebar-background": "#142033",
        "color-sidebar-background-border": "#253a57",
        "color-sidebar-brand-text": "#f1f5f9",
        "color-sidebar-caption-text": "#8da2bb",
        "color-sidebar-link-text": "#d0dbe7",
        "color-sidebar-link-text--top-level": "#60a5fa",

        "color-sidebar-search-background": "#0f1a2a",
        "color-sidebar-search-background--focus": "#17263d",
        "color-sidebar-search-text": "#f1f5f9",
        "color-sidebar-search-border": "#314761",
        "color-sidebar-search-icon": "#8da2bb",

        "color-inline-code-background": "#e2e8f0",
        "color-highlighted-background": "#dbeafe",
        "color-admonition-background": "#eef6ff",
        "color-guilabel-background": "#dbeafe80",
        "color-guilabel-border": "#93c5fd80",
        "color-table-header-background": "#dde6f1",
    },

    "dark_css_variables": {
        "color-foreground-primary": "#e6edf7",
        "color-foreground-secondary": "#a9b7c8",
        "color-foreground-muted": "#7b8798",
        "color-foreground-border": "#3b4a5f",

        "color-background-primary": "#090f18",
        "color-background-secondary": "#0f1724",
        "color-background-hover": "#172236",
        "color-background-border": "#25344a",

        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#93c5fd",
        "color-brand-visited": "#a78bfa",

        "color-sidebar-background": "#050914",
        "color-sidebar-background-border": "#1e2d44",
        "color-sidebar-brand-text": "#f8fafc",
        "color-sidebar-caption-text": "#7b8da5",
        "color-sidebar-link-text": "#c6d3e2",
        "color-sidebar-link-text--top-level": "#60a5fa",

        "color-sidebar-search-background": "#0f1724",
        "color-sidebar-search-background--focus": "#172236",
        "color-sidebar-search-text": "#e6edf7",
        "color-sidebar-search-border": "#25344a",
        "color-sidebar-search-icon": "#7b8da5",

        "color-inline-code-background": "#141d2b",
        "color-highlighted-background": "#1e3a5f",
        "color-admonition-background": "#101a2a",
        "color-guilabel-background": "#1e3a5f80",
        "color-guilabel-border": "#60a5fa40",
        "color-table-header-background": "#141d2b",
    },
    "sidebar_hide_name": True,
    "light_logo": "logo_dark.svg",
    "dark_logo": "logo_dark.svg",
    "navigation_with_keys": True,
    "announcement": "This documentation is under active development.",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_extra_path = ['_static']

# -- Auto-generated API pages ------------------------------------------------

import importlib.util

def _run_doc_generator(script_name: str) -> None:
    path = os.path.join(os.path.dirname(__file__), script_name)
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.generate()


_run_doc_generator("generate_cable_database_rst.py")

