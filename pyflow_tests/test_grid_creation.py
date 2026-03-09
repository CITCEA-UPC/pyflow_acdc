import pyflow_acdc as pyf


def run_test():
    """Test grid creation functionality."""

    pyf.initialize_pyflowacdc()

    S_base = 100

    AC_node_1 = pyf.Node_AC(node_type='Slack', Voltage_0=1.06, theta_0=0, kV_base=345)
    AC_node_2 = pyf.Node_AC(node_type='PV', Voltage_0=1, theta_0=0.1, kV_base=345,Power_Gained=0.4,Power_load=0.2,Reactive_load=0.1)
    AC_node_3 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.45,Reactive_load=0.15)
    AC_node_4 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.4,Reactive_load=0.05)
    AC_node_5 = pyf.Node_AC(node_type='PQ', Voltage_0=1, theta_0=0.1, kV_base=345,Power_load=0.6,Reactive_load=0.1)

    AC_line_1 = pyf.Line_AC(AC_node_1, AC_node_2,r=0.02,x=0.06,b=0.06,MVA_rating=150)
    AC_line_2 = pyf.Line_AC(AC_node_1, AC_node_3,r=0.08,x=0.24,b=0.05,MVA_rating=100)
    AC_line_3 = pyf.Line_AC(AC_node_2, AC_node_3,r=0.06,x=0.18,b=0.04,MVA_rating=100)
    AC_line_4 = pyf.Line_AC(AC_node_2, AC_node_4,r=0.06,x=0.18,b=0.04,MVA_rating=100)
    AC_line_5 = pyf.Line_AC(AC_node_2, AC_node_5,r=0.04,x=0.12,b=0.03,MVA_rating=100)
    AC_line_6 = pyf.Line_AC(AC_node_3, AC_node_4,r=0.01,x=0.03,b=0.02,MVA_rating=100)   
    AC_line_7 = pyf.Line_AC(AC_node_4, AC_node_5,r=0.08,x=0.24,b=0.05,MVA_rating=100)

    DC_node_1 = pyf.Node_DC(node_type='P', Voltage_0=1,kV_base=345)
    DC_node_2 = pyf.Node_DC(node_type='Slack', Voltage_0=1,kV_base=345)
    DC_node_3 = pyf.Node_DC(node_type='P', Voltage_0=1,kV_base=345)

    DC_line_1 = pyf.Line_DC(DC_node_1, DC_node_2,r=0.052,MW_rating=100,polarity='sm')
    DC_line_2 = pyf.Line_DC(DC_node_2, DC_node_3,r=0.052,MW_rating=100,polarity='sm')
    DC_line_3 = pyf.Line_DC(DC_node_1, DC_node_3,r=0.073,MW_rating=100,polarity='sm')

    Converter_1 = pyf.AC_DC_converter('PQ', 'PAC'  , AC_node_2, DC_node_1, P_AC=-0.6, Q_AC=-0.4, P_DC=0, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)
    Converter_2 = pyf.AC_DC_converter('PV', 'Slack', AC_node_3, DC_node_2, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)
    Converter_3 = pyf.AC_DC_converter('PQ', 'PAC'  , AC_node_5, DC_node_3, P_AC=0.35, Q_AC=0.05, Transformer_resistance=0.0015, Transformer_reactance=0.121, Phase_Reactor_R=0.0001, Phase_Reactor_X=0.16428, Filter=0.0887, Droop=0, kV_base=345, MVA_max=120)

    AC_nodes = [AC_node_1, AC_node_2, AC_node_3, AC_node_4, AC_node_5]
    DC_nodes = [DC_node_1, DC_node_2, DC_node_3]
    AC_lines = [AC_line_1, AC_line_2, AC_line_3, AC_line_4, AC_line_5, AC_line_6, AC_line_7]
    DC_lines = [DC_line_1, DC_line_2, DC_line_3]
    Converters = [Converter_1, Converter_2, Converter_3]


    grid = pyf.Grid(S_base,AC_nodes, AC_lines,Converters,DC_nodes, DC_lines)
    res= pyf.Results(grid,decimals=3)


    pyf.ACDC_sequential(grid)

    res.All()


def test_grid_creation():
    """Pytest entrypoint for grid creation test."""
    run_test()


if __name__ == "__main__":
    run_test()
