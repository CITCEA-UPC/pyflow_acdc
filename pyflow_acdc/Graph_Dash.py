# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 12:03:23 2024

@author: BernardoCastro
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots

__all__ = [
    'run_dash',
    'run_ts_dash',
    'run_mp_ts_dash',
    'create_mp_ts_dash',
    'plot_TS_res_from_ts',
]

_MP_PLOT_CHOICES = [
    'Power Generation by price zone',
    'Power Generation by generator',
    'Power Generation by price zone area chart',
    'Power Generation by generator area chart',
    'Market Prices',
    'PN_min',
    'PN_max',
    'AC line loading',
    'DC line loading',
    'AC/DC Converters',
    'Curtailment',
]


def _get_df_and_label_from_ts(time_series_results, S_base, plotting_choice):
    """Resolve (dataframe, y-axis label) from a time_series_results mapping (not grid)."""
    if plotting_choice == 'Curtailment':
        return time_series_results['curtailment'] * 100, 'Curtailment %'
    if plotting_choice == 'PN_min':
        df = time_series_results.get('PN_min')
        return df, 'PN_min (MW)' if df is not None else ''
    if plotting_choice == 'PN_max':
        df = time_series_results.get('PN_max')
        return df, 'PN_max (MW)' if df is not None else ''
    if plotting_choice in ['Power Generation by generator', 'Power Generation by generator area chart']:
        return time_series_results['real_power_opf'] * S_base, 'Power Generation (MW)'
    if plotting_choice in ['Power Generation by price zone', 'Power Generation by price zone area chart']:
        return time_series_results['real_power_by_zone'] * S_base, 'Power Generation (MW)'
    if plotting_choice == 'Market Prices':
        df = time_series_results['prices_by_zone']
        df = df.loc[:, ~df.columns.str.startswith('o_')]
        return df, 'Market Prices (€/MWh)'
    if plotting_choice == 'AC line loading':
        return time_series_results['ac_line_loading'] * 100, 'AC Line Loading %'
    if plotting_choice == 'DC line loading':
        return time_series_results['dc_line_loading'] * 100, 'DC Line Loading %'
    if plotting_choice == 'AC/DC Converters':
        return time_series_results['converter_loading'] * 100, 'AC/DC Converters loading %'
    return None, ''


def _get_df_and_label(grid, plotting_choice):
    return _get_df_and_label_from_ts(grid.time_series_results, grid.S_base, plotting_choice)


def plot_TS_res_from_ts(
    time_series_results,
    S_base,
    plotting_choice,
    selected_rows,
    x_limits=None,
    y_limits=None,
    show_title=True,
    legend_prefix='',
):
    """Build one Plotly figure from stored TS results (e.g. one investment period)."""
    df, y_label = _get_df_and_label_from_ts(time_series_results, S_base, plotting_choice)
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=(f"Time Series: {plotting_choice}" if show_title else None),
            xaxis_title="Time",
            yaxis_title=y_label if y_label else "Value"
        )
        return fig

    time = df.index

    fig = go.Figure()
    cumulative_sum = None
    stack_areas = plotting_choice in ['Power Generation by generator area chart', 'Power Generation by price zone area chart']

    # Custom color palette
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    for i, col in enumerate(selected_rows):
        if col in df.columns:
            y_values = df[col]
            color = colors[i % len(colors)]
            trace_name = f'{legend_prefix}{col}' if legend_prefix else col

            if stack_areas:
                if cumulative_sum is None:
                    cumulative_sum = y_values.copy()
                    fig.add_trace(
                        go.Scatter(x=time, y=y_values, name=trace_name, hoverinfo='x+y+name', 
                                 fill='tozeroy', line=dict(color=color), fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.5])}')
                    )
                else:
                    y_values = cumulative_sum + y_values
                    cumulative_sum = y_values
                    fig.add_trace(
                        go.Scatter(x=time, y=y_values, name=trace_name, hoverinfo='x+y+name',
                                 fill='tonexty', line=dict(color=color), fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.5])}')
                    )
            else:
                fig.add_trace(
                    go.Scatter(x=time, y=y_values, name=trace_name, hoverinfo='x+y+name',
                             line=dict(color=color, width=2))
                )

    # Enhanced layout
    title_block = None
    if show_title:
        title_block = dict(
            text=f"Time Series: {plotting_choice}",
            font=dict(size=24, color="#2c3e50"),
            x=0.5,
            xanchor='center',
        )
    fig.update_layout(
        title=title_block,
        xaxis_title=dict(text="Time", font=dict(size=14)),
        yaxis_title=dict(text=y_label, font=dict(size=14)),
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
        margin=dict(l=60, r=30, t=80, b=60),
        showlegend=True,
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#2c3e50',
            borderwidth=1
        )
    )

    # Grid styling
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#e1e1e1',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='#2c3e50'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='#e1e1e1',
        zeroline=True,
        zerolinewidth=1,
        zerolinecolor='#2c3e50'
    )

    if x_limits is None:
        x_limits = (df.index[0], df.index[-1])
    fig.update_xaxes(range=x_limits)
    
    if y_limits and len(y_limits) == 2:
        fig.update_yaxes(range=y_limits)

    return fig


def plot_TS_res(grid, plotting_choice, selected_rows, x_limits=None, y_limits=None):
    return plot_TS_res_from_ts(
        grid.time_series_results,
        grid.S_base,
        plotting_choice,
        selected_rows,
        x_limits=x_limits,
        y_limits=y_limits,
        show_title=True,
        legend_prefix='',
    )


def create_dash_app(grid):
    app = dash.Dash(__name__)

    # Custom CSS for better styling
    app.layout = html.Div(style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '20px',
        'fontFamily': 'Arial, sans-serif',
        'backgroundColor': '#f5f6fa'
    }, children=[
        html.H1(f"{grid.name} Time Series Dashboard", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
        
        # First Plot Controls
        html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
            html.H3("Plot 1", style={'color': '#2c3e50', 'marginBottom': '15px'}),
            html.Label("Select Plot Type:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.Dropdown(
                id='plotting-choice-1',
                options=[
                    {'label': 'Power Generation by price zone', 'value': 'Power Generation by price zone'},
                    {'label': 'Power Generation by generator', 'value': 'Power Generation by generator'},
                    {'label': 'Power Generation by price zone area chart', 'value': 'Power Generation by price zone area chart'},
                    {'label': 'Power Generation by generator area chart', 'value': 'Power Generation by generator area chart'},
                    {'label': 'Market Prices', 'value': 'Market Prices'},
                    {'label': 'AC line loading', 'value': 'AC line loading'},
                    {'label': 'DC line loading', 'value': 'DC line loading'},
                    {'label': 'AC/DC Converters', 'value': 'AC/DC Converters'},
                    {'label': 'Curtailment', 'value': 'Curtailment'}
                ],
                value='Power Generation by price zone',
                style={'marginBottom': '20px'}
            ),
            
            html.Label("Select Components:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.Checklist(
                id='subplot-selection-1',
                options=[],
                value=[],
                inline=True,
                style={'marginBottom': '20px'}
            ),
            
            html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
                html.Div(style={'flex': 1}, children=[
                    html.Label('Y-axis limits:', style={'fontWeight': 'bold'}),
                    html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
                        dcc.Input(id='y-min-1', type='number', placeholder='Min', value=0, style={'flex': 1, 'padding': '5px'}),
                        dcc.Input(id='y-max-1', type='number', placeholder='Max', value=100, style={'flex': 1, 'padding': '5px'})
                    ])
                ])
            ])
        ]),

        # Toggle for second plot
        html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
            html.Label("Show Second Plot:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
            dcc.RadioItems(
                id='show-plot-2',
                options=[
                    {'label': 'Yes', 'value': True},
                    {'label': 'No', 'value': False}
                ],
                value=False,
                inline=True
            )
        ]),

        # Second Plot Controls (hidden by default)
        html.Div(id='plot-2-controls', style={'display': 'none'}, children=[
            html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
                html.H3("Plot 2", style={'color': '#2c3e50', 'marginBottom': '15px'}),
                html.Label("Select Plot Type:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='plotting-choice-2',
                    options=[
                        {'label': 'Power Generation by price zone', 'value': 'Power Generation by price zone'},
                        {'label': 'Power Generation by generator', 'value': 'Power Generation by generator'},
                        {'label': 'Power Generation by price zone area chart', 'value': 'Power Generation by price zone area chart'},
                        {'label': 'Power Generation by generator area chart', 'value': 'Power Generation by generator area chart'},
                        {'label': 'Market Prices', 'value': 'Market Prices'},
                        {'label': 'AC line loading', 'value': 'AC line loading'},
                        {'label': 'DC line loading', 'value': 'DC line loading'},
                        {'label': 'AC/DC Converters', 'value': 'AC/DC Converters'},
                        {'label': 'Curtailment', 'value': 'Curtailment'}
                    ],
                    value='Market Prices',
                    style={'marginBottom': '20px'}
                ),
                
                html.Label("Select Components:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Checklist(
                    id='subplot-selection-2',
                    options=[],
                    value=[],
                    inline=True,
                    style={'marginBottom': '20px'}
                ),
                
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
                    html.Div(style={'flex': 1}, children=[
                        html.Label('Y-axis limits:', style={'fontWeight': 'bold'}),
                        html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
                            dcc.Input(id='y-min-2', type='number', placeholder='Min', value=0, style={'flex': 1, 'padding': '5px'}),
                            dcc.Input(id='y-max-2', type='number', placeholder='Max', value=100, style={'flex': 1, 'padding': '5px'})
                        ])
                    ])
                ])
            ])
        ]),

        # Common X-axis controls
        html.Div(style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '20px'}, children=[
            html.Label('X-axis limits:', style={'fontWeight': 'bold'}),
            html.Div(style={'display': 'flex', 'gap': '10px'}, children=[
                dcc.Input(id='x-min', type='number', placeholder='Min', style={'flex': 1, 'padding': '5px'}),
                dcc.Input(id='x-max', type='number', placeholder='Max', style={'flex': 1, 'padding': '5px'})
            ])
        ]),
        
        # Plots
        html.Div(style={
            'backgroundColor': 'white',
            'padding': '20px',
            'borderRadius': '10px',
            'marginTop': '20px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }, children=[
            dcc.Graph(id='plot-output-1'),
            html.Div(id='plot-2-container', style={'display': 'none'}, children=[
                dcc.Graph(id='plot-output-2')
            ])
        ])
    ])

    @app.callback(
        [Output('plot-2-controls', 'style'),
         Output('plot-2-container', 'style')],
        [Input('show-plot-2', 'value')]
    )
    def toggle_plot_2(show_plot_2):
        if show_plot_2:
            return {'display': 'block'}, {'display': 'block'}
        return {'display': 'none'}, {'display': 'none'}

    @app.callback(
        [Output('subplot-selection-1', 'options'),
         Output('subplot-selection-1', 'value'),
         Output('subplot-selection-2', 'options'),
         Output('subplot-selection-2', 'value')],
        [Input('plotting-choice-1', 'value'),
         Input('plotting-choice-2', 'value')]
    )
    def update_subplot_options(plotting_choice_1, plotting_choice_2):
        def get_columns(plotting_choice):
            df, _ = _get_df_and_label(grid, plotting_choice)
            if df is None or df.empty:
                return []
            return df.columns.tolist()

        cols_1 = get_columns(plotting_choice_1)
        cols_2 = get_columns(plotting_choice_2)
        
        options_1 = [{'label': col, 'value': col} for col in cols_1]
        options_2 = [{'label': col, 'value': col} for col in cols_2]
        
        return options_1, cols_1, options_2, cols_2

    @app.callback(
        [Output('y-min-1', 'value'),
         Output('y-max-1', 'value'),
         Output('y-min-2', 'value'),
         Output('y-max-2', 'value')],
        [Input('plotting-choice-1', 'value'),
         Input('plotting-choice-2', 'value')]
    )
    def update_limits(plotting_choice_1, plotting_choice_2):
        def get_limits(plotting_choice):
            data, _ = _get_df_and_label(grid, plotting_choice)
            if data is None:
                return 0, 1

            if not data.empty:
                y_min = int(min(0, data.min().min() - 5))
                if plotting_choice in ['Power Generation by generator area chart', 'Power Generation by price zone area chart']:
                    cumulative_sum = data.sum(axis=1)
                    y_max = int(cumulative_sum.max() + 10)
                elif plotting_choice in ['AC line loading', 'DC line loading', 'Curtailment']:
                    y_max = int(min(data.max().max() + 10, 100))
                else:
                    y_max = int(data.max().max() + 10)
                return y_min, y_max
            return 0, 1

        y_min_1, y_max_1 = get_limits(plotting_choice_1)
        y_min_2, y_max_2 = get_limits(plotting_choice_2)
        
        return y_min_1, y_max_1, y_min_2, y_max_2

    @app.callback(
        [Output('plot-output-1', 'figure'),
         Output('plot-output-2', 'figure')],
        [Input('plotting-choice-1', 'value'),
         Input('plotting-choice-2', 'value'),
         Input('subplot-selection-1', 'value'),
         Input('subplot-selection-2', 'value'),
         Input('x-min', 'value'),
         Input('x-max', 'value'),
         Input('y-min-1', 'value'),
         Input('y-max-1', 'value'),
         Input('y-min-2', 'value'),
         Input('y-max-2', 'value'),
         Input('show-plot-2', 'value')]
    )
    def update_graphs(plotting_choice_1, plotting_choice_2, selected_rows_1, selected_rows_2, 
                     x_min, x_max, y_min_1, y_max_1, y_min_2, y_max_2, show_plot_2):
        x_limits = (x_min, x_max) if x_min is not None and x_max is not None else None
        y_limits_1 = (y_min_1, y_max_1) if y_min_1 is not None and y_max_1 is not None else None
        y_limits_2 = (y_min_2, y_max_2) if y_min_2 is not None and y_max_2 is not None else None
        
        fig1 = plot_TS_res(grid, plotting_choice_1, selected_rows_1, x_limits=x_limits, y_limits=y_limits_1)
        
        # Only create second plot if it's enabled
        if show_plot_2:
            fig2 = plot_TS_res(grid, plotting_choice_2, selected_rows_2, x_limits=x_limits, y_limits=y_limits_2)
        else:
            fig2 = go.Figure()  # Empty figure when plot 2 is disabled
        
        return fig1, fig2

    return app


def _ts_inv_usable(grid):
    ts_inv = getattr(grid, 'ts_inv', None)
    return isinstance(ts_inv, dict) and bool(ts_inv)


def run_ts_dash(grid, debug=True, use_reloader=False):
    """Run the single-grid TS Dash app (requires ``grid.Time_series_ran``)."""
    app = create_dash_app(grid)
    app.run(debug=debug, use_reloader=use_reloader)


def run_dash(grid, debug=True, use_reloader=False):
    """
    Start the appropriate Dash app from grid run flags (same family as ``Grid.reset_run_flags``).

    * ``grid.dash_mode`` optional: ``'auto'`` (default), ``'mp_ts'``, or ``'single_ts'``.

    **auto** (precedence):

    1. ``MP_TEP_run`` or ``MP_MS_TEP_run`` and ``grid.ts_inv`` populated (MS TS-OPF post-processing)
       → multi-period TS dashboard.
    2. Else ``Time_series_ran`` → single-grid TS dashboard.
    3. Else raise ``ValueError``.
    """
    mode = getattr(grid, 'dash_mode', 'auto')
    if mode not in ('auto', 'mp_ts', 'single_ts'):
        mode = 'auto'

    if mode == 'mp_ts':
        if not _ts_inv_usable(grid):
            raise ValueError('run_dash: dash_mode=mp_ts requires grid.ts_inv from MS TS-OPF (run_opf_for_all_investment_periods MS=True).')
        return run_mp_ts_dash(
            grid.ts_inv,
            grid_name=getattr(grid, 'name', 'grid'),
            debug=debug,
            use_reloader=use_reloader,
        )
    if mode == 'single_ts':
        return run_ts_dash(grid, debug=debug, use_reloader=use_reloader)

    # auto
    if (getattr(grid, 'MP_TEP_run', False) or getattr(grid, 'MP_MS_TEP_run', False)) and _ts_inv_usable(grid):
        return run_mp_ts_dash(
            grid.ts_inv,
            grid_name=getattr(grid, 'name', 'grid'),
            debug=debug,
            use_reloader=use_reloader,
        )
    if getattr(grid, 'Time_series_ran', False):
        return run_ts_dash(grid, debug=debug, use_reloader=use_reloader)

    raise ValueError(
        'run_dash (auto): need either (MP_TEP_run or MP_MS_TEP_run) with grid.ts_inv, '
        'or Time_series_ran after TS_ACDC_OPF. Override with grid.dash_mode=\'mp_ts\' or \'single_ts\'.'
    )


def create_mp_ts_dash(ts_inv, grid_name='MP time series'):
    """
    Dash app for TS results saved per investment period (see run_opf_for_all_investment_periods MS mode).

    ts_inv: mapping with optional ``'base'`` (nominal np) and int keys for MP periods;
    values are ``{'time_series_results': ..., 'S_base': float, ...}``.
    """
    if not ts_inv:
        raise ValueError('ts_inv is empty')

    has_base = 'base' in ts_inv
    int_periods = sorted(k for k in ts_inv.keys() if isinstance(k, int))
    if not has_base and not int_periods:
        raise ValueError('ts_inv has no period keys')

    def _period_order():
        out = []
        if has_base:
            out.append('base')
        out.extend(int_periods)
        return out

    period_order = _period_order()

    plot_dd_options = [{'label': x, 'value': x} for x in _MP_PLOT_CHOICES]

    def _ref_snapshot():
        return ts_inv[period_order[0]]

    def _columns_for(plot_type, ref_snap):
        df, _ = _get_df_and_label_from_ts(
            ref_snap['time_series_results'], ref_snap['S_base'], plot_type
        )
        if df is None or df.empty:
            return [], []
        cols = df.columns.tolist()
        return [{'label': c, 'value': c} for c in cols], cols

    period_opts = []
    for p in period_order:
        if p == 'base':
            period_opts.append({'label': 'Base (nominal np)', 'value': 'base'})
        else:
            period_opts.append({'label': f'Period {p}', 'value': p})
    period_opts_skip = period_opts + [{'label': '—', 'value': -1}]

    def _default_triple():
        a = period_order[0]
        b = period_order[min(1, len(period_order) - 1)]
        c = period_order[min(2, len(period_order) - 1)]
        return a, b, c

    d1, d2, d3 = _default_triple()

    app = dash.Dash(__name__)
    app.layout = html.Div(style={
        'maxWidth': '1400px',
        'margin': '0 auto',
        'padding': '20px',
        'fontFamily': 'Arial, sans-serif',
        'backgroundColor': '#f5f6fa',
    }, children=[
        html.H1(f'{grid_name} — TS by investment period', style={'textAlign': 'center', 'color': '#2c3e50'}),
        dcc.RadioItems(
            id='mp-mode',
            options=[
                {'label': 'Single period', 'value': 'single'},
                {'label': 'Compare three periods (columns)', 'value': 'compare'},
            ],
            value='single',
            inline=True,
            style={'marginBottom': '16px'},
        ),
        html.Div(id='mp-single-row', children=[
            html.Label('Period:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='mp-period-single',
                options=period_opts,
                value=period_order[0],
                clearable=False,
                style={'marginBottom': '12px'},
            ),
        ]),
        html.Div(id='mp-compare-row', style={'display': 'none'}, children=[
            html.Div(style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'}, children=[
                html.Div(style={'flex': 1, 'minWidth': '180px'}, children=[
                    html.Label('Column 1', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='mp-p1', options=period_opts_skip, value=d1, clearable=False),
                ]),
                html.Div(style={'flex': 1, 'minWidth': '180px'}, children=[
                    html.Label('Column 2', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='mp-p2', options=period_opts_skip, value=d2, clearable=False),
                ]),
                html.Div(style={'flex': 1, 'minWidth': '180px'}, children=[
                    html.Label('Column 3', style={'fontWeight': 'bold'}),
                    dcc.Dropdown(id='mp-p3', options=period_opts_skip, value=d3, clearable=False),
                ]),
            ]),
        ]),
        html.Label('Plot type:', style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='mp-plot-type',
            options=plot_dd_options,
            value='Power Generation by price zone',
            style={'marginBottom': '12px'},
        ),
        html.Label('Series:', style={'fontWeight': 'bold'}),
        dcc.Checklist(id='mp-cols', options=[], value=[], inline=True, style={'marginBottom': '16px'}),
        html.Div(style={'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap', 'marginBottom': '12px'}, children=[
            html.Div(style={'display': 'flex', 'gap': '6px', 'alignItems': 'center'}, children=[
                html.Span('X min:'), dcc.Input(id='mp-xmin', type='number', placeholder='auto', style={'width': '100px'}),
                html.Span('X max:'), dcc.Input(id='mp-xmax', type='number', placeholder='auto', style={'width': '100px'}),
            ]),
            html.Div(style={'display': 'flex', 'gap': '6px', 'alignItems': 'center'}, children=[
                html.Span('Y min:'), dcc.Input(id='mp-ymin', type='number', placeholder='auto', style={'width': '100px'}),
                html.Span('Y max:'), dcc.Input(id='mp-ymax', type='number', placeholder='auto', style={'width': '100px'}),
            ]),
        ]),
        dcc.Graph(id='mp-graph', style={'height': '560px'}),
    ])

    @app.callback(
        [Output('mp-compare-row', 'style'),
         Output('mp-single-row', 'style')],
        [Input('mp-mode', 'value')],
    )
    def _toggle_mode(mode):
        if mode == 'compare':
            return {'display': 'block'}, {'display': 'none'}
        return {'display': 'none'}, {'display': 'block'}

    @app.callback(
        [Output('mp-cols', 'options'),
         Output('mp-cols', 'value')],
        [Input('mp-plot-type', 'value'),
         Input('mp-mode', 'value'),
         Input('mp-period-single', 'value')],
    )
    def _update_cols(plot_type, mode, period_single):
        ref = _ref_snapshot()
        if mode == 'single' and period_single is not None and period_single in ts_inv:
            ref = ts_inv[period_single]
        opts, cols = _columns_for(plot_type, ref)
        return opts, cols

    @app.callback(
        Output('mp-graph', 'figure'),
        [Input('mp-mode', 'value'),
         Input('mp-period-single', 'value'),
         Input('mp-p1', 'value'),
         Input('mp-p2', 'value'),
         Input('mp-p3', 'value'),
         Input('mp-plot-type', 'value'),
         Input('mp-cols', 'value'),
         Input('mp-xmin', 'value'),
         Input('mp-xmax', 'value'),
         Input('mp-ymin', 'value'),
         Input('mp-ymax', 'value')],
    )
    def _update_mp_fig(mode, ps, p1, p2, p3, plot_type, cols, xmin, xmax, ymin, ymax):
        cols = cols or []
        x_limits = (xmin, xmax) if xmin is not None and xmax is not None else None
        y_limits = (ymin, ymax) if ymin is not None and ymax is not None else None

        if mode == 'single':
            if ps is None or ps not in ts_inv:
                fig = go.Figure()
                fig.update_layout(title='Invalid period')
                return fig
            snap = ts_inv[ps]
            return plot_TS_res_from_ts(
                snap['time_series_results'],
                snap['S_base'],
                plot_type,
                cols,
                x_limits=x_limits,
                y_limits=y_limits,
                show_title=True,
                legend_prefix='',
            )

        titles = []
        for p in (p1, p2, p3):
            if p == -1:
                titles.append('—')
            elif p == 'base':
                titles.append('Base (nominal np)')
            else:
                titles.append(f'Period {p}')
        fig = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=titles,
            shared_yaxes=True,
        )
        any_trace = False
        for ci, p in enumerate((p1, p2, p3)):
            if p == -1 or p not in ts_inv:
                continue
            snap = ts_inv[p]
            sub = plot_TS_res_from_ts(
                snap['time_series_results'],
                snap['S_base'],
                plot_type,
                cols,
                x_limits=x_limits,
                y_limits=y_limits,
                show_title=False,
                legend_prefix='',
            )
            for tr in sub.data:
                fig.add_trace(tr, row=1, col=ci + 1)
                any_trace = True
        if not any_trace:
            fig.add_annotation(
                text='Select at least one period column',
                xref='paper',
                yref='paper',
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        fig.update_layout(
            height=520,
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=True,
            margin=dict(l=50, r=30, t=80, b=50),
        )
        if x_limits is not None:
            for c in range(1, 4):
                fig.update_xaxes(range=x_limits, row=1, col=c)
        if y_limits is not None:
            fig.update_yaxes(range=y_limits, row=1, col=1)
        return fig

    return app


def run_mp_ts_dash(ts_inv, grid_name='MP time series', debug=True, use_reloader=False):
    app = create_mp_ts_dash(ts_inv, grid_name=grid_name)
    app.run(debug=debug, use_reloader=use_reloader)

