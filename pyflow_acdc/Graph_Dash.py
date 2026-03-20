# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 12:03:23 2024

@author: BernardoCastro
"""

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

__all__ = [
    'run_dash'
]

def _get_df_and_label(grid, plotting_choice):
    if plotting_choice == 'Curtailment':
        return grid.time_series_results['curtailment'] * 100, 'Curtailment %'
    if plotting_choice in ['Power Generation by generator', 'Power Generation by generator area chart']:
        return grid.time_series_results['real_power_opf'] * grid.S_base, 'Power Generation (MW)'
    if plotting_choice in ['Power Generation by price zone', 'Power Generation by price zone area chart']:
        return grid.time_series_results['real_power_by_zone'] * grid.S_base, 'Power Generation (MW)'
    if plotting_choice == 'Market Prices':
        df = grid.time_series_results['prices_by_zone']
        df = df.loc[:, ~df.columns.str.startswith('o_')]
        return df, 'Market Prices (€/MWh)'
    if plotting_choice == 'AC line loading':
        return grid.time_series_results['ac_line_loading'] * 100, 'AC Line Loading %'
    if plotting_choice == 'DC line loading':
        return grid.time_series_results['dc_line_loading'] * 100, 'DC Line Loading %'
    if plotting_choice == 'AC/DC Converters':
        return grid.time_series_results['converter_loading'] * 100, 'AC/DC Converters loading %'
    return None, ''

def plot_TS_res(grid, plotting_choice, selected_rows, x_limits=None, y_limits=None):
    # Select the appropriate DataFrame based on plotting_choice
   
    df, y_label = _get_df_and_label(grid, plotting_choice)
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f"Time Series: {plotting_choice}",
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

            if stack_areas:
                if cumulative_sum is None:
                    cumulative_sum = y_values.copy()
                    fig.add_trace(
                        go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name', 
                                 fill='tozeroy', line=dict(color=color), fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.5])}')
                    )
                else:
                    y_values = cumulative_sum + y_values
                    cumulative_sum = y_values
                    fig.add_trace(
                        go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name',
                                 fill='tonexty', line=dict(color=color), fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.5])}')
                    )
            else:
                fig.add_trace(
                    go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name',
                             line=dict(color=color, width=2))
                )

    # Enhanced layout
    fig.update_layout(
        title=dict(
            text=f"Time Series: {plotting_choice}",
            font=dict(size=24, color="#2c3e50"),
            x=0.5,
            xanchor='center'
        ),
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

def run_dash(grid, debug=True, use_reloader=False):
    app = create_dash_app(grid)
    app.run(debug=debug, use_reloader=use_reloader)

