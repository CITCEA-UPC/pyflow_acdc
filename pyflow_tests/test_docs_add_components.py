# -*- coding: utf-8 -*-
"""
Test for adding components example from documentation.
Tests the "Adding Components" section in usage.rst
"""

import pyflow_acdc as pyf


def test_docs_add_components():
    """Pytest entrypoint for docs add components example."""
    run_test()


def run_test():
    """Test adding components example from documentation."""

    pyf.initialize_pyflowacdc()

    # Create core grid first as shown in docs
    grid = pyf.Grid(100)
    res = pyf.Results(grid)

    # Add AC nodes as shown in docs
    ac_node_1 = pyf.add_AC_node(grid, node_type='Slack', Voltage_0=1.06, theta_0=0, kV_base=345)
    ac_node_2 = pyf.add_AC_node(grid, node_type='PV', Voltage_0=1, theta_0=0.1, kV_base=345, Power_Gained=0.4, Power_load=0.2, Reactive_load=0.1)
    ac_node_3 = pyf.add_AC_node(grid, node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345, Power_load=0.45, Reactive_load=0.15)
    ac_node_4 = pyf.add_AC_node(grid, node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345, Power_load=0.4, Reactive_load=0.05)
    ac_node_5 = pyf.add_AC_node(grid, node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345, Power_load=0.6, Reactive_load=0.1)

    # Add AC lines as shown in docs
    ac_line_1 = pyf.add_line_AC(grid, ac_node_1, ac_node_2, r=0.02, x=0.06, b=0.06, MVA_rating=150)
    ac_line_2 = pyf.add_line_AC(grid, ac_node_1, ac_node_3, r=0.08, x=0.24, b=0.05, MVA_rating=100)
    ac_line_3 = pyf.add_line_AC(grid, ac_node_2, ac_node_3, r=0.06, x=0.18, b=0.04, MVA_rating=100)
    ac_line_4 = pyf.add_line_AC(grid, ac_node_2, ac_node_4, r=0.06, x=0.18, b=0.04, MVA_rating=100)
    ac_line_5 = pyf.add_line_AC(grid, ac_node_2, ac_node_5, r=0.04, x=0.12, b=0.03, MVA_rating=100)
    ac_line_6 = pyf.add_line_AC(grid, ac_node_3, ac_node_4, r=0.01, x=0.03, b=0.02, MVA_rating=100)
    ac_line_7 = pyf.add_line_AC(grid, ac_node_4, ac_node_5, r=0.08, x=0.24, b=0.05, MVA_rating=100)

    # Add DC nodes as shown in docs
    dc_node_1 = pyf.add_DC_node(grid, node_type='P', Voltage_0=1, kV_base=345)
    dc_node_2 = pyf.add_DC_node(grid, node_type='Slack', Voltage_0=1, kV_base=345)
    dc_node_3 = pyf.add_DC_node(grid, node_type='P', Voltage_0=1, kV_base=345)

    # Add DC lines as shown in docs
    dc_line_1 = pyf.add_line_DC(grid, dc_node_1, dc_node_2, r=0.052, MW_rating=100, polarity='sm')
    dc_line_2 = pyf.add_line_DC(grid, dc_node_2, dc_node_3, r=0.052, MW_rating=100, polarity='sm')
    dc_line_3 = pyf.add_line_DC(grid, dc_node_1, dc_node_3, r=0.073, MW_rating=100, polarity='sm')

    # Add converters as shown in docs
    converter_1 = pyf.add_ACDC_converter(grid, ac_node_2, dc_node_1, 'PQ', 'PAC', P_AC_MW=-60, Q_AC_MVA=-40, 
                                        Transformer_resistance=0.0015, Transformer_reactance=0.121, 
                                        Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, 
                                        Droop=0, kV_base=345, MVA_max=120)
    converter_2 = pyf.add_ACDC_converter(grid, ac_node_3, dc_node_2, 'PV', 'Slack', 
                                        Transformer_resistance=0.0015, Transformer_reactance=0.121, 
                                        Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, 
                                        Droop=0, kV_base=345, MVA_max=120)
    converter_3 = pyf.add_ACDC_converter(grid, ac_node_5, dc_node_3, 'PQ', 'PAC', P_AC_MW=35, Q_AC_MVA=5, 
                                        Transformer_resistance=0.0015, Transformer_reactance=0.121, 
                                        Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, 
                                        Droop=0, kV_base=345, MVA_max=120)

    # Run power flow as shown in docs
    time,tol,ps_iterations = pyf.ACDC_sequential(grid)
    res.All()

    print("✓ Add components test passed")

if __name__ == "__main__":
    run_test()