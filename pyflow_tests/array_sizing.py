# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 09:50:14 2025

@author: BernardoCastro
"""

import pyflow_acdc as pyf

def array_sizing(combinations):

    S_base=100
    WACC=0.06
    FLH = 4500

    LCoE = 79
    power_rating = 9.5
    FLH=4500
    # Define the combinations to run




    # Loop through each combination
    for combo in combinations:

        print(f'Starting analysis with opt_type={combo["opt_type"]}, Nc={combo["Nc"]}')
        print('--------------------------------------------------------------')
        opt_type = combo['opt_type']
        Nc = combo['Nc']
        
        # Set gamma limit based on FLH
        if opt_type == 'W' or opt_type == 'FLH':
            gamma_limit = 0.9
        elif opt_type == 'OPF':
            gamma_limit = 0
        else:
            gamma_limit = 1


        grid,res = pyf.Create_grid_from_data(S_base)




        SS = pyf.add_AC_node(grid, kV_base=66,node_type='Slack',name='SS')
        T1 = pyf.add_AC_node(grid, kV_base=66,name='T1')
        T2 = pyf.add_AC_node(grid, kV_base=66,name='T2')
        T3 = pyf.add_AC_node(grid, kV_base=66,name='T3')
        T4 = pyf.add_AC_node(grid, kV_base=66,name='T4')
        T5 = pyf.add_AC_node(grid, kV_base=66,name='T5')
        T6 = pyf.add_AC_node(grid, kV_base=66,name='T6')
        T7 = pyf.add_AC_node(grid, kV_base=66,name='T7')
        T8 = pyf.add_AC_node(grid, kV_base=66,name='T8')
        #T9 = pyf.add_AC_node(grid, kV_base=66,name='T9')

        pyf.add_RenSource(grid,'T1', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T2', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T3', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T4', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T5', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T6', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T7', power_rating,min_gamma=gamma_limit,Qrel=0.3)
        pyf.add_RenSource(grid,'T8', power_rating,min_gamma=gamma_limit,Qrel=0.3)

        pyf.add_extGrid(grid, 'SS',lf=LCoE)

        # ABB_Cu_XLPE_95mm²_66kV    34  145
        # ABB_Cu_XLPE_120mm2_66kV   38  157    
        # ABB_Cu_XLPE_150mm2_66kV   42  171
        # ABB_Cu_XLPE_185mm2_66kV   48  188
        # ABB_Cu_XLPE_240mm2_66kV   55  215
        # ABB_Cu_XLPE_300mm2_66kV   60  244
        # ABB_Cu_XLPE_400mm2_66kV   67  292
        # ABB_Cu_XLPE_500mm2_66kV   75  340
        # ABB_Cu_XLPE_630mm2_66kV   81  403  
        # ABB_Cu_XLPE_800mm2_66kV   88  485
        # ABB_Cu_XLPE_1000mm2_66kV  94  581

        
        LT8_T7=1.4
        LT7_T6=1.4
        LT6_T5=1.4
        LT5_T4=1.1
        LT4_T3=1.2
        LT3_T2=1.5
        LT2_T1=1.5
        LT1_SS=3.0


        cable_option = pyf.add_cable_option(grid,[
            'ABB_XLPE_Cu_66kV_sub_95mm2',
            'ABB_XLPE_Cu_66kV_sub_120mm2',
            'ABB_XLPE_Cu_66kV_sub_150mm2',
            'ABB_XLPE_Cu_66kV_sub_185mm2',
            'ABB_XLPE_Cu_66kV_sub_240mm2',
            'ABB_XLPE_Cu_66kV_sub_300mm2',
            'ABB_XLPE_Cu_66kV_sub_400mm2',
            'ABB_XLPE_Cu_66kV_sub_500mm2',
            'ABB_XLPE_Cu_66kV_sub_630mm2',
            'ABB_XLPE_Cu_66kV_sub_800mm2',
            'ABB_XLPE_Cu_66kV_sub_1000mm2'],'PEI')

        pyf.add_line_sizing(grid,T8,T7,cable_option=cable_option.name,active_config=0,Length_km=LT8_T7,name='T8_T7',update_grid=False)
        pyf.add_line_sizing(grid,T7,T6,cable_option=cable_option.name,active_config=0,Length_km=LT7_T6,name='T7_T6',update_grid=False)
        pyf.add_line_sizing(grid,T6,T5,cable_option=cable_option.name,active_config=0,Length_km=LT6_T5,name='T6_T5',update_grid=False)
        pyf.add_line_sizing(grid,T5,T4,cable_option=cable_option.name,active_config=1,Length_km=LT5_T4,name='T5_T4',update_grid=False)
        pyf.add_line_sizing(grid,T4,T3,cable_option=cable_option.name,active_config=3,Length_km=LT4_T3,name='T4_T3',update_grid=False)
        pyf.add_line_sizing(grid,T3,T2,cable_option=cable_option.name,active_config=5,Length_km=LT3_T2,name='T3_T2',update_grid=False)
        pyf.add_line_sizing(grid,T2,T1,cable_option=cable_option.name,active_config=6,Length_km=LT2_T1,name='T2_T1',update_grid=False)
        pyf.add_line_sizing(grid,T1,SS,cable_option=cable_option.name,active_config=8,Length_km=LT1_SS,name='T1_SS',update_grid=False)
        

        grid.create_Ybus_AC()
        grid.Update_Graph_AC()


        # pyf.AC_PowerFlow(grid)
        # res.TEP_N()


        obj = {'Energy_cost': 1}
        grid.cab_types_allowed = Nc



        if opt_type == 'OPF':
            model, timing_info, model_res,solver_stats= pyf.Optimal_PF(grid,ObjRule=obj)
            res.All()
            res.TEP_N()
            res.OBJ_res()
        
        elif opt_type == 'FLH':
            model, model_results , timing_info, solver_stats= pyf.transmission_expansion(grid,NPV=True,Hy=FLH,discount_rate=WACC,ObjRule=obj,tee=True)
            res.TEP_N()
            res.TEP_norm()
            model.obj.display()
        else:
            model, model_results , timing_info, solver_stats= pyf.transmission_expansion(grid,NPV=True,discount_rate=WACC)
            res.All()

        
        print(timing_info)

def run_test():
    """Test array sizing functionality."""
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    
    try:
        import pyomo.environ as pyo
        solver = pyo.SolverFactory('bonmin')
        if not solver.available():
            raise ImportError("Bonmin solver not available")
    except (ImportError, Exception):
        print("Bonmin solver is not available. To use TEP functions, please install Bonmin solver.")
        return

    combinations = [
        {'opt_type': 'FLH', 'Nc': 1},
        {'opt_type': 'FLH', 'Nc': 2},
        {'opt_type': 'FLH', 'Nc': 3},
        {'opt_type': 'FLH', 'Nc': 4},
    ]
    array_sizing(combinations)

if __name__ == "__main__":
    run_test()