"""Price-zone market coefficients from order-book and ENTSO-E data.

Builds quadratic **benefit-of-consumption** and **cost-of-generation** curves
for :class:`~pyflow_acdc.Classes.Price_Zone` OPF/TEP models from:

* **EPEX Spot**-shaped intraday order books (supply/demand stacks per hour).
* **ENTSO-E Transparency** CSV exports (generation by type and day-ahead load),
  normalized to hourly profiles for time-series studies.

Typical workflow::

    market_data, timing = price_zone_coef_data(order_book_df, start=1, end=8760)
    coef_table = price_zone_data_pd(market_data, save_csv="pz_coef.csv")
    plot_curves(market_data, hour=12, name="Zone A")  # optional inspection

See :doc:`market_coef` and :ref:`Price_zone_modelling`.
"""

import re
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from scipy.integrate import quad
from scipy.interpolate import interp1d
from scipy.optimize import minimize

__all__ = [
    'price_zone_data_pd',
    'price_zone_coef_data',
    'plot_curves',
    'clean_entsoe_data'
    ]

def price_zone_data_pd(data, save_csv=None):
    """Flatten :func:`price_zone_coef_data` output to a coefficient table.

    Parameters
    ----------
    data : list[dict]
        One dict per hour from :func:`price_zone_coef_data`. Each dict must
        contain ``Hour``, ``poly`` (with ``a_BC``, ``b_BC``, ``c_BC``, ``a_CG``,
        ``b_CG``, ``c_CG``, ``P_min``, ``P_max``), ``Market_price``, and
        ``Volume_eq``.
    save_csv : str, optional
        If given, write the table to CSV. ``.csv`` is appended when missing.

    Returns
    -------
    pandas.DataFrame
        Indexed by hour (``time``). Columns: quadratic coefficients, clearing
        price/volume, and power limits ``PGL_min`` / ``PGL_max``.
    """

    rows = []
    for i in data:
        hour = i['Hour']
        a_BC = i['poly']['a_BC']
        b_BC = i['poly']['b_BC']
        c_BC = i['poly']['c_BC']
        a_CG = i['poly']['a_CG']
        b_CG = i['poly']['b_CG']
        c_CG = i['poly']['c_CG']
        price = i['Market_price']
        volume = i['Volume_eq']
        PGL_min = i['poly']['P_min']
        PGL_max = i['poly']['P_max']
        rows.append({
            'time': hour,
            'a_BC': a_BC,
            'b_BC': b_BC,
            'c_BC': c_BC,
            'a_CG': a_CG,
            'b_CG': b_CG,
            'c_CG': c_CG,
            'price': price,
            'volume': volume,
            'PGL_min': PGL_min,
            'PGL_max': PGL_max,
        })

    df = pd.DataFrame(rows).set_index('time')
    if save_csv is not None:
        if save_csv.endswith('.csv'):
            df.to_csv(save_csv, index=True)
        else:
            df.to_csv(f'{save_csv}.csv', index=True)
    return df

def is_leap_year(year):
    """Check if a year is a leap year."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def price_zone_coef_data(df, start, end, increase_eq_price=50):
    """Fit price-zone quadratic coefficients from an EPEX-shaped order book.

    Parses stacked sell/purchase curves per calendar hour, finds the market
    clearing point, integrates surplus areas, and fits ``a``, ``b``, ``c``
    polynomials for benefit-of-consumption and cost-of-generation (see
    :ref:`Price_zone_modelling`).

    Parameters
    ----------
    df : pandas.DataFrame or str
        Order-book table, or path to a CSV with the columns below.
    start : int
        First hour of year to process (1-based, inclusive).
    end : int
        Last hour of year to process (1-based, inclusive).
    increase_eq_price : float, optional
        Artificial price increment (€/MWh) used when extending supply curves
        for high clearing prices (default ``50``).

    Returns
    -------
    small_data : list[dict]
        One entry per hour in ``[start, end]``. Each dict includes:

        * ``Sell``, ``Purchase`` — order-book DataFrames (``volume``, ``price``).
        * ``Integrated_sets`` — integrated welfare components.
        * ``Market_price``, ``Volume_eq`` — clearing price and volume.
        * ``poly`` — dict with ``a_BC``, ``b_BC``, ``c_BC``, ``a_CG``, ``b_CG``,
          ``c_CG``, ``P_min``, ``P_max``.
        * ``prediction_BC``, ``prediction_CG`` — fitted curve samples.
    timing_info : dict
        Keys ``load data``, ``avg process``, ``tot process`` (seconds).

    Notes
    -----
    **Expected CSV columns** (EPEX Spot export style):

    * ``Date`` — ``DD/MM/YYYY``
    * ``Hour`` — integer hour, or ``3B`` style label on DST fall-back
    * ``Volume``, ``Price`` — MW and €/MWh
    * ``C3``, ``C4`` — optional metadata (ignored)
    * ``Sale/Purchase`` — ``Sell`` or ``Purchase`` (column name must be exactly
      this so :func:`pandas.DataFrame.itertuples` exposes it as ``row._6``)

    DST spring/fall transitions are handled via hour labels and an internal
    summer-time offset.

    Examples
    --------
    >>> import pandas as pd
    >>> import pyflow_acdc as pyf
    >>> rows = [
    ...     {"Date": "01/01/2023", "Hour": 1, "Volume": 50, "Price": 30,
    ...      "C3": 0, "C4": 0, "Sale/Purchase": "Sell"},
    ...     {"Date": "01/01/2023", "Hour": 1, "Volume": 50, "Price": 80,
    ...      "C3": 0, "C4": 0, "Sale/Purchase": "Purchase"},
    ... ]
    >>> data, _ = pyf.price_zone_coef_data(pd.DataFrame(rows), start=1, end=1)
    >>> "poly" in data[0]
    True
    """

    if isinstance(df, str):
        df= pd.read_csv(df)

    first_date = pd.to_datetime(df.iloc[0]['Date'], format='%d/%m/%Y')
    year = first_date.year
    is_leap = is_leap_year(year)
    total_hours = 8784 if is_leap else 8760

    data = [
    {
        'Date': None,  # Placeholder for the date
        'Hour': i,
        'Sell': pd.DataFrame(columns=['volume', 'price']),
        'Purchase': pd.DataFrame(columns=['volume', 'price'])
    }
    for i in range(1, total_hours + 1)
    ]

    min_hour= total_hours
    max_hour=1
    hour_prev = df.iloc[0]['Hour']
    date_prev = df.iloc[0]['Date']
    summer_time_offset = 0
    dst_active = False
    data_storage = {'Sell': [[] for _ in range(total_hours)], 'Purchase': [[] for _ in range(total_hours)], 'Dates': [None] * total_hours}
    t1= time.perf_counter()

    for row in df.itertuples(index=False):

        # print(row)
        date = row.Date
        hour = row.Hour

        # print(f'{date}----{dst_active}')
        # Detect DST changes and handle "B" hour (e.g., "3B")
        if "B" not in str(hour):
            try:
                if date == date_prev and abs(int(hour) - int(hour_prev)) > 1 and not dst_active:
                    # Spring forward (e.g., 2 -> 4), activate summer time offset

                    summer_time_offset = -1
                    hour_prev = int(hour) - 1  # Ensure hour is an integer for calculations
                    # print(hour)
                    dst_active = True
            except ValueError:
                # Handle the case where the conversion to int fails
                print(f'Subtraction not possible at {hour}')
        elif "B" in str(hour):
            # Autumn fallback, remove summer time offset
            summer_time_offset = 0
            hour = int(hour.replace("B", ""))  # Convert "3B" to 3, or any "XB" to X
            dst_active = False

        volume = row.Volume
        if volume==0:
            continue
        price = row.Price
        Sale_purchase = row._6


        date_obj = pd.to_datetime(date, format='%d/%m/%Y')
        day_of_year = date_obj.dayofyear
        # print(date)
        # print(hour)
        hour_of_year = (day_of_year - 1) * 24 + int(hour) + summer_time_offset
        # print(hour_of_year)

        # point= (week*7+week_day)*24+hour+24
        min_hour=min(min_hour,hour_of_year)
        max_hour=max(max_hour,hour_of_year)
        # Append the new row to the appropriate DataFrame
        data_storage[Sale_purchase][hour_of_year - 1].append({'volume': volume, 'price': price})
        data_storage['Dates'][hour_of_year - 1] = date


        date_prev = date
        hour_prev = hour

    for i in range(8760):
        data[i]['Date'] = data_storage['Dates'][i]
        data[i]['Sell'] = pd.DataFrame(data_storage['Sell'][i])
        data[i]['Purchase'] = pd.DataFrame(data_storage['Purchase'][i])

    t2= time.perf_counter()
    t_loaddata = t2-t1

    min_hour=max(min_hour,start)
    max_hour=min(max_hour,end)


    small_data=data[min_hour-1: max_hour]
    count = 0

    for entry in small_data:
        if not entry['Sell'].empty:
            entry['Gen_data_points']= entry['Sell']['volume'].count()
            entry['max_gen'] = entry['Sell']['volume'].max()
        else:
            entry['max_gen'] = 0

        if not entry['Purchase'].empty:
            entry['Dem_data_points']= entry['Purchase']['volume'].count()
            entry['min_demand'] = entry['Purchase']['volume'].min()
        else:
            entry['min_demand'] = 0
        hour= entry['Hour']

        cost_generation_curve(data, hour,increase_eq_price)
        count+=1
        # print(hour)


    t3 = time.perf_counter()
    t_process = t3-t2
    t_avprocess = t_process/count
    timing_info = {
    "load data": t_loaddata,
    "avg process": t_avprocess,
    "tot process": t_process }
    return small_data , timing_info



def cost_generation_curve(data, hour,increase_eq_price):
    chosen_entry, supply_df, demand_df, eq_volume, eq_price,volumes , supply_interp, demand_interp,min_volume,max_volume = prepare_data_and_interpolate(data, hour)

    max_price=eq_price+increase_eq_price
    if max_price<10:
        max_price = 10
    # Calculate benefits and costs separately
    coefficients_BC, volume_linspace_demand,cumulative_benefit_interp = calculate_benefit_of_consumption(demand_df, eq_volume, demand_interp,min_volume,max_volume,eq_price,max_price)
    coefficients_CG, volume_linspace_supply,cumulative_cost_interp ,min_volume_s,first_positive_volume= calculate_cost_of_generation(supply_df, min_volume,eq_volume,max_volume,max_price, supply_interp,eq_price)

    a_CG = coefficients_CG[0]
    b_CG = coefficients_CG[1]
    c_CG = coefficients_CG[2]

    a_BC = coefficients_BC[0]
    b_BC = coefficients_BC[1]
    c_BC = coefficients_BC[2]

    P_min_curve= -b_CG/(2*a_CG)
    P_min_data =min_volume_s-eq_volume
    P_max= volume_linspace_supply[-1]

    P_min=max(P_min_data,P_min_curve)


    if P_min >0:
        P_min=0
    if P_max<0:
        P_max=0

    volume_linspace_supply = np.linspace(P_min,P_max, num=100)

    #Price is determined as the derivation of cost of generation
    price = 2*a_CG*(volume_linspace_supply)+b_CG

    cumulative_cost_values_all = cumulative_cost_interp(volumes)
    cumulative_benefit_values_all = cumulative_benefit_interp(volumes)

    net_benefit_all =  cumulative_benefit_values_all - cumulative_cost_values_all


    chosen_entry['Integrated_sets'] = pd.DataFrame({
        'volume': volumes,
        'cost_of_generation_values': cumulative_cost_values_all,
        'social_welfare_all':net_benefit_all,
        'benefit_of_consumption_values': cumulative_benefit_values_all})

    chosen_entry['prediction_BC'] = pd.DataFrame({
        'Volume_surplus_values': volume_linspace_demand,
        'real_benefit_prodcution':cumulative_benefit_interp(volume_linspace_demand+eq_volume) ,
        'predicted_benefit_consumption': np.polyval([a_BC, b_BC, c_BC], volume_linspace_demand)
    })

    chosen_entry['prediction_CG'] = pd.DataFrame({
        'Volume_surplus_values': volume_linspace_supply,
        'real_cost_gen' : cumulative_cost_interp(volume_linspace_supply+eq_volume) ,
        'predicted_cost_of_gen': np.polyval([a_CG, b_CG, 0], volume_linspace_supply),
        'price':price
    })


    chosen_entry['poly'] = {
        'a_BC': a_BC,
        'b_BC': b_BC,
        'c_BC': c_BC,
        'a_CG': a_CG,
        'b_CG': b_CG,
        'c_CG': c_CG,
        'P_min': P_min,  # Minimum power output
        'P_max': P_max,  # Maximum power output
    }


    chosen_entry['Market_price'] = eq_price
    chosen_entry['Volume_eq'] = eq_volume
    chosen_entry['Volume_0'] = first_positive_volume


    return coefficients_BC, coefficients_CG



def prepare_data_and_interpolate(data, hour):
    chosen_entry = data[hour - 1]
    supply_data = chosen_entry['Sell']
    demand_data = chosen_entry['Purchase']

    supply_df = pd.DataFrame(supply_data).groupby('volume').mean().reset_index()
    demand_df = pd.DataFrame(demand_data).groupby('volume').mean().reset_index()
    # print(hour-1)
    min_volume = max(min(supply_df['volume']), min(demand_df['volume']))
    max_volume = min(max(supply_df['volume']), max(demand_df['volume']))

    volumes = np.linspace(min_volume, max_volume, num=1000)

    supply_interp = interp1d(supply_df['volume'], supply_df['price'], kind='linear', fill_value="extrapolate")
    demand_interp = interp1d(demand_df['volume'], demand_df['price'], kind='linear', fill_value="extrapolate")

    price_diff = supply_interp(volumes) - demand_interp(volumes)
    nan_indices = np.isnan(price_diff)
    price_diff = price_diff[~nan_indices]
    volumes = volumes[~nan_indices]

    eq_index = np.argmin(np.abs(price_diff))
    eq_volume = volumes[eq_index]
    eq_price = supply_interp(eq_volume).item()


    return chosen_entry, supply_df, demand_df, eq_volume, eq_price,volumes , supply_interp, demand_interp,min_volume,max_volume


def calculate_benefit_of_consumption(demand_df, eq_volume, demand_interp,min_volume,max_volume,eq_price,max_price):
    cumulative_benfit = [0]
    for i in range(1, len(demand_df)):
        V_prev = demand_df['volume'][i-1]
        V = demand_df['volume'][i]
        benefit_of_consumption, _ = quad(lambda x: demand_interp(x), V_prev, V)
        cumulative_benfit.append(cumulative_benfit[-1] + benefit_of_consumption)

    demand_df['cumulative_benefit'] = cumulative_benfit

    positive_demand_df = demand_df[demand_df['price'] > 0]



    filtered_demand_df = demand_df[demand_df['price'] < max_price]
    last_positive_price_vol = positive_demand_df['volume'].iloc[-1]
    volume_at_max_price = filtered_demand_df['volume'].iloc[0]


    if eq_price >0:
        max_volume_s= last_positive_price_vol
    else:
        max_volume_s=max_volume



    cumulative_benefit_interp = interp1d(demand_df['volume'], demand_df['cumulative_benefit'], fill_value="extrapolate")
    volume_linspace_demand   = np.linspace(volume_at_max_price, max_volume_s, num=100)
    BC_gain_values =  cumulative_benefit_interp(volume_linspace_demand)

    #shifting demand to equilibrium point
    # volume_linspace_demand-=eq_volume
    coefficients_BC = np.polyfit(volume_linspace_demand, BC_gain_values, 2)

    return coefficients_BC, volume_linspace_demand ,cumulative_benefit_interp

def calculate_cost_of_generation(supply_df, min_volume,eq_volume,max_volume,max_price, supply_interp,eq_price):
    cumulative_cost = [0]

    for i in range(1, len(supply_df)):
        V_prev = supply_df['volume'][i-1]
        V = supply_df['volume'][i]
        cost_of_generation, _ = quad(lambda x: supply_interp(x), V_prev, V)
        cumulative_cost.append(cumulative_cost[-1] + cost_of_generation)

    supply_df['cumulative_cost'] = cumulative_cost

    positive_supply_df = supply_df[supply_df['price'] > 1]
    first_positive_price_index = supply_df[supply_df['price'] > 0].index[0]
    first_positive_volume = supply_df.loc[first_positive_price_index, 'volume']

    def fit_with_vertex_constraint(coeffs):
        # Coefficients of the quadratic: y = ax^2 + bx + c
        a, b, c = coeffs

        # Compute the vertex x-coordinate: x = -b / (2a)
        vertex_x = -b / (2 * a)

        # Compute the quadratic fit values
        fitted_curve = a * volume_linspace_supply**2 + b * volume_linspace_supply + c

        # Calculate the error in fitting
        fit_error = np.sum((fitted_curve - CG_cost_values) ** 2)/ len(CG_cost_values)

        # Add a penalty for the vertex not aligning with the first positive volume
        vertex_penalty = (vertex_x - first_positive_volume) ** 2

        # Combine the fit error and the penalty
        penalty_weight = 10  # Adjust this weight to balance the fit and vertex alignment
        # print("Fitting Error:", fit_error)
        # print("Penalty:", vertex_penalty)
        return fit_error + penalty_weight * vertex_penalty

    filtered_supply_df = supply_df[supply_df['price'] < max_price]

    if positive_supply_df.index[0] > 0:  # Ensure there is a previous index
        if eq_price <100:
            previous_price_vol = supply_df['volume'].iloc[positive_supply_df.index[0]]
        else:
            previous_price_vol = supply_df['volume'].iloc[positive_supply_df.index[0]]
    else:
        previous_price_vol = supply_df['volume'].iloc[positive_supply_df.index[0]]



    first_positive_price_vol=previous_price_vol
    volume_at_max_price = filtered_supply_df['volume'].iloc[-1]


    if eq_price >0:
        min_volume_s= first_positive_price_vol
    else:
        min_volume_s=eq_volume
    # max_volume_s=min(volume_at_max_price,max_volume)

    cumulative_cost_interp = interp1d(supply_df['volume'], supply_df['cumulative_cost'], fill_value="extrapolate")
    volume_linspace_supply = np.linspace(min_volume_s,volume_at_max_price, num=100)
    CG_cost_values =  cumulative_cost_interp(volume_linspace_supply)


    #shifting supply to equilibrium point
    volume_linspace_supply-=eq_volume
    # coefficients_CG = np.polyfit(volume_linspace_supply, CG_cost_values, 2)

    # Initial guess for coefficients [a, b, c]
    initial_guess = np.polyfit(volume_linspace_supply, CG_cost_values, 2)

    if eq_price >15:
        bounds = [(1e-5, None),  # 'a' > 0 (positive)
              (1e-5, np.inf),  # 'b' can be any real number
              (-np.inf, np.inf)]  # 'c' can be any real number
        # Optimise the fit
        result = minimize(fit_with_vertex_constraint, initial_guess, bounds=bounds,method='L-BFGS-B')
        # Extract optimised coefficients
        optimized_coeffs = result.x
        a_CG, b_CG, c_CG = optimized_coeffs
        coefficients_CG = optimized_coeffs
    else:
        coefficients_CG = initial_guess
    return coefficients_CG, volume_linspace_supply,cumulative_cost_interp,min_volume_s,first_positive_volume




def plot_curves(data, hour, name=None):
    """Plot supply, demand, and price-zone curves for one hour.

    Parameters
    ----------
    data : list[dict]
        Output of :func:`price_zone_coef_data`.
    hour : int
        Hour to plot (1-based index into ``data``).
    name : str, optional
        Price-zone label shown in the plot title.

    Notes
    -----
    Opens the figure in a web browser via Plotly (``renderer='browser'``).
    In tests, patch ``pyflow_acdc.Market_Coeff.pio.show`` to capture the figure
    without a GUI.

    Returns
    -------
    plotly.graph_objects.Figure
        The generated figure (also opened in the browser).

    Examples
    --------
    >>> import pyflow_acdc as pyf
    >>> market_data = pyf.price_zone_coef_data(df, start=1, end=24)
    >>> pyf.plot_curves(market_data, hour=12, name='Belgium')
    """
    chosen_entry = data[hour - 1]
    # Extract Sell, Purchase, and Social Cost data
    sell_data = chosen_entry['Sell']
    purchase_data = chosen_entry['Purchase']
    intSet = chosen_entry['Integrated_sets']
    pcg = chosen_entry['prediction_CG']

    curve_data= chosen_entry['poly']
    # Create a subplot figure with 2 rows and 1 column
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True, vertical_spacing=0.1, column_widths=[0.7, 0.3],
                        subplot_titles=('Supply and Demand', 'Cost of Generation', 'Integrated supply and demand','Price'))

    eq_price=chosen_entry['Market_price']
    eq_volume= chosen_entry['Volume_eq']

    c_CG=curve_data['c_CG']

    # Add scatter trace for Sell data
    if not sell_data.empty:
        fig.add_trace(go.Scatter(x=sell_data['volume'], y=sell_data['price'], mode='lines+markers', name='Supply'), row=1, col=1)

    # Add scatter trace for Purchase data
    if not purchase_data.empty:
        fig.add_trace(go.Scatter(x=purchase_data['volume'], y=purchase_data['price'], mode='lines+markers', name='Demand'), row=1, col=1)

    if not sell_data.empty and not  purchase_data.empty:
        # Add vertical line at equilibrium volume
        fig.add_trace(go.Scatter(x=[eq_volume, eq_volume], y=[min(min(sell_data['price']), min(purchase_data['price'])),
                                                              max(max(sell_data['price']), max(purchase_data['price']))],
                                 mode='lines', line=dict(color='Green', width=2, dash='dash'), name='Equilibrium Volume'), row=1, col=1)

        # Add horizontal line at equilibrium price
        fig.add_trace(go.Scatter(x=[min(min(sell_data['volume']), min(purchase_data['volume'])),
                                    max(max(sell_data['volume']), max(purchase_data['volume']))],
                                 y=[eq_price, eq_price],
                                 mode='lines', line=dict(color='Red', width=2, dash='dash'), name='Equilibrium Price'), row=1, col=1)

    # Add scatter trace for Social Cost data
    if not intSet.empty:
        fig.add_trace(go.Scatter(x=intSet['volume'], y=intSet['cost_of_generation_values'], mode='lines+markers', name='Cost of Gen'), row=2, col=1)
        fig.add_trace(go.Scatter(x=intSet['volume'], y=intSet['benefit_of_consumption_values'], mode='lines+markers', name='Benefit of consumption'), row=2, col=1)
        fig.add_trace(go.Scatter(x=intSet['volume'], y=intSet['social_welfare_all'], mode='lines+markers', name='Social Welfare'), row=2, col=1)

        # fig.add_trace(go.Scatter(x=pbc['Volume_surplus_values'], y=pbc['predicted_benefit_consumption'], mode='lines+markers', name='predicted_benefit_consumption'), row=2, col=1)


        fig.add_trace(go.Scatter(x=pcg['Volume_surplus_values'], y=pcg['real_cost_gen']-c_CG, mode='lines+markers', name='Cost of Generation'), row=1, col=2)
        fig.add_trace(go.Scatter(x=pcg['Volume_surplus_values'], y=pcg['predicted_cost_of_gen'], mode='lines+markers', name='Predicted cost of gen'), row=1, col=2)

        fig.add_trace(go.Scatter(x=pcg['Volume_surplus_values'], y=pcg['price'], mode='lines+markers', name='Predicted price CoG'), row=2, col=2)

    mp = np.round(chosen_entry['Market_price'], decimals=2)
    # Add vertical line at equilibrium volume and horizontal line at equilibrium price


    for line_data, line_color, line_name in [ #(eq_volume-curve_data['shift'],'Green',''),
                                            (curve_data['P_min'] , 'Blue', 'P min'),
                                              (curve_data['P_max'] , 'Blue', 'P max')]:
        fig.add_trace(go.Scatter(x=[line_data, line_data],
                                  y=[min(pcg['price']),
                                    max(pcg['price'])],
                                  mode='lines', line=dict(color=line_color, width=2, dash='dash'), name=line_name), row=2, col=2)



    # Update layout with titles and axis labels
    if name is not None:
        fig.update_layout(        title=f'Supply and Demand for hour {hour}; Market Price: {mp}, Price Zone: {name}'           )

    else:
        fig.update_layout(        title=f'Supply and Demand for hour {hour}; Market Price: {mp}'           )

    # Update xaxis properties
    fig.update_xaxes(title_text="Volume [MWh]", row=2, col=1)
    fig.update_xaxes(title_text="P balance = Gen - Load [MW]", row=2, col=2)

    # Update yaxis properties
    fig.update_yaxes(title_text="Offer Price [€/MWh]", row=1, col=1)
    fig.update_yaxes(title_text="Social Cost [€]", row=1, col=2)
    fig.update_yaxes(title_text="Integrated [€]", row=2, col=1)
    fig.update_yaxes(title_text="Market Price [€]", row=2, col=2)



    # Display the figure in a web browser
    pio.show(fig, renderer='browser')

    return fig


### ENTSEO DATA


def compute_hour_of_year(df,production_types=None, Area= None):
    # Filter the dataframe based on the production type if provided
    if production_types is None:
        production_types = []

    mtu_substring='MTU'

    if production_types and isinstance(production_types, list):
        # Handle non-empty list case
        production_types = [pt.strip() for pt in production_types]
        df = df[df["Production Type"].isin(production_types)].reset_index(drop=True)
        num_prod = len(production_types)
        if df.empty:
           print("The DataFrame is empty after filtering. Check the production_types or the data.")
           return df
    elif production_types == 'Load':
        num_prod = 1
    else:
        # Handle empty list, None, or invalid input
        production_types = list(df['Production Type'].unique())
        num_prod = len(production_types)
    # Find the column that contains 'MTU' in its name (case-insensitive match)
    mtu_columns = [col for col in df.columns if mtu_substring in col.upper()]

    MW_cols = [col for col in df.columns if 'MW' in col.upper()]
    for MW_col in MW_cols:
        df[MW_col] = pd.to_numeric(df[MW_col], errors='coerce')



    if mtu_columns:
        # Use the first column that contains 'MTU'
        mtu_column = mtu_columns[0]
        print(f"Found MTU column: {mtu_column}")
        numeric_cols = df.select_dtypes(include='number').columns
        sample_time = df[mtu_column].iloc[0]

        # Try to find a valid time range using regex
        time_pattern = r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}) - (\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})"
        match = re.match(time_pattern, sample_time)

        if match:
            # Extract start and end times from the MTU string
            start_time = pd.to_datetime(match.group(1))
            end_time = pd.to_datetime(match.group(2))

            # Compute the time difference in hours
            time_diff = (end_time - start_time).total_seconds() / 3600  # In hours

            if time_diff == 1:  # 1-hour step
                df['Hour of Year'] = (df.index//num_prod) + 1
            elif time_diff == 0.5:  # 30-minute step
                df['Hour of Year'] = (df.index // 2*num_prod) + 1
            elif time_diff == 0.25:  # 15-minute step
                df['Hour of Year'] = (df.index // 4*num_prod) + 1
            else:
                print(f"Unknown time step in {mtu_column}. Please check the MTU column.")
                df['Hour of Year'] = df.index + 1

        else:
            print(f"MTU column in {mtu_column} does not match expected time range format.")
            df['Hour of Year'] = df.index + 1



        if isinstance(production_types, list):
            # Pivot the data to have each production type as a separate column
            df = df.pivot_table(index='Hour of Year', columns="Production Type", values=numeric_cols, aggfunc="mean")

            # Flatten the multi-level column index if necessary
            df.columns = [f"{prod_type}" for col, prod_type in df.columns]
            df = df.reset_index()
        numeric_cols = df.select_dtypes(include='number').columns
        # Check the time step by inspecting the time format in the first row


    else:
        print("No MTU-like column found in the dataframe.")
        df['Hour of Year'] = df.index + 1


    df_hourly = df.groupby('Hour of Year')[numeric_cols].mean()

    all_hours = set(range(1, df['Hour of Year'].max() + 1))  # Create a set of all possible hours
    existing_hours = set(df['Hour of Year'])  # Set of hours already in the dataframe
    missing_hours = all_hours - existing_hours  # Set of missing hou
    if missing_hours:
        missing_df = pd.DataFrame({'Hour of Year': list(missing_hours)})
        for col in df_hourly.columns:
            if col != 'Hour of Year':  # Set all other columns to NaN
                missing_df[col] = np.nan

        # Step 3: Append the missing rows to the original dataframe
        df_hourly = pd.concat([df_hourly, missing_df]).sort_values(by='Hour of Year').reset_index(drop=True)


    df_hourly = df_hourly.set_index('Hour of Year')
    if 'Hour of Year' in df_hourly.columns:
        df_hourly = df_hourly.drop(columns=['Hour of Year'])
    df_hourly = df_hourly.interpolate(method='linear', axis=0)
    df_hourly = df_hourly.bfill(axis=0).ffill(axis=0)


    max_values = df_hourly.max()

    # Create a dictionary with column names as keys and max values as values
    max_dict = {col: max_values[col] for col in df_hourly.columns}

    # Step 2: Normalize each column by dividing by its max value
    df_normalized = df_hourly.copy()  # Make a copy to avoid changing the original df
    for col in df_hourly.columns:
        df_normalized[col] = df_hourly[col] / max_dict[col]

    if Area is not None:
        df_normalized.columns = [f'{Area}_' + col for col in df_normalized.columns]
    # Return the resulting DataFrame with hourly data
    return df_normalized, max_dict




def clean_entsoe_data(key_list, year_list, production_types=None, output_excel=None, path=None):
    """Normalize ENTSO-E generation/load CSVs and write an Excel workbook.

    Reads per-area folders of ENTSO-E Transparency exports, resamples to hourly
    profiles (via :func:`compute_hour_of_year`), normalizes by annual maxima, and
    writes one sheet per year plus a ``Maximum Values`` summary.

    Parameters
    ----------
    key_list : list[str]
        Subfolder names under ``path`` (one per bidding zone / area).
    year_list : list[int]
        Years to process. Expects files named like
        ``AGGREGATED_GENERATION_PER_TYPE_GENERATION_{y-1}12312300-{y}12312300.csv``
        and ``GUI_TOTAL_LOAD_DAYAHEAD_{y-1}12312300-{y}12312300.csv`` in each
        area folder.
    production_types : list[str], optional
        Generation types to keep. Empty list means all types in the file.
    output_excel : str, optional
        Output ``.xlsx`` filename (default ``output_data.xlsx``).
    path : str, optional
        Root directory containing area subfolders. When ``None``, paths are
        relative to the current working directory.

    Returns
    -------
    str
        Path to the written Excel file.

    Notes
    -----
    Folder layout is documented in :doc:`market_coef`. Files must match ENTSO-E
    download naming; MTU columns are detected automatically for 15/30/60 minute
    data.
    """
    if production_types is None:
        production_types = []
    combined_dict_all = {}
    combined_df_all = {}

    for year in year_list:
        combined_dict_year = {}
        combined_df_year = pd.DataFrame()
        for key in key_list:
                if path is None:
                    name_GEN= f"{key}/AGGREGATED_GENERATION_PER_TYPE_GENERATION_{year-1}12312300-{year}12312300"
                    name_Load= f"{key}/GUI_TOTAL_LOAD_DAYAHEAD_{year-1}12312300-{year}12312300"
                else:
                    name_GEN= f"{path}/{key}/AGGREGATED_GENERATION_PER_TYPE_GENERATION_{year-1}12312300-{year}12312300"
                    name_Load= f"{path}/{key}/GUI_TOTAL_LOAD_DAYAHEAD_{year-1}12312300-{year}12312300"
                # Read the data
                df_GEN = pd.read_csv(f"{name_GEN}.csv")
                df_Load = pd.read_csv(f"{name_Load}.csv")

                # Apply the function to df_GEN and df_Load
                df_GEN_hourly , max_dict_gen = compute_hour_of_year(df_GEN, production_types, Area= key)
                df_Load_hourly, max_dict_load = compute_hour_of_year(df_Load, Area= key)


                # Combine the data from df_GEN_hourly and df_Load_hourly
                combined_df = pd.merge(df_GEN_hourly, df_Load_hourly, on='Hour of Year', how='outer')
                combined_dict = {**max_dict_gen, **max_dict_load}

                combined_dict_year[key]=combined_dict
                if combined_df_year.empty:  # Check if it's the first iteration
                    combined_df_year = combined_df  # Initialize with the first combined_df
                else:
                    combined_df_year = pd.merge(combined_df_year, combined_df, left_index=True, right_index=True, how='outer')

        combined_dict_all[year] = combined_dict_year
        combined_df_all[year]   = combined_df_year

    if output_excel is None:
        output_excel= "output_data.xlsx"
    else:
        if not output_excel.endswith('.xlsx'):
            output_excel= f"{output_excel}.xlsx"
    if path is not None:
        output_excel= f"{path}/{output_excel}"

    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        # Write combined_dict_all to a single sheet with separate tables for each year
        sheet_name = "Maximum Values"
        if sheet_name not in writer.sheets:
            writer.book.create_sheet(sheet_name)
        start_row = 0  # Initialize starting row for writing tables
        for year, combined_dict in combined_dict_all.items():
            # Convert the year's dictionary to a DataFrame

            year_df = pd.DataFrame()

            # Iterate over the areas dictionary to add each area's data as a column
            for area, dicts in combined_dict.items():
                area_df = pd.DataFrame.from_dict(dicts, orient='index', columns=[area])
                if year_df.empty:
                    year_df = area_df
                else:
                    year_df = pd.merge(year_df, area_df, left_index=True, right_index=True, how='outer')

            # Write a header for the year
            header_df = pd.DataFrame([f"Table for Year {year}"], columns=[""])
            header_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=False, header=False)

            start_row += 1

            # Write the DataFrame
            year_df.to_excel(writer, sheet_name=sheet_name, startrow=start_row, index=True)
            start_row += len(area_df) + 3  # Leave a blank row between tables

        # Write each year's combined_df_all to a separate sheet
        for idx, year in enumerate(combined_df_all.keys(), start=1):
            combined_df_all[year].to_excel(writer, sheet_name=f"{year}", index=True)

    return output_excel
