import pyflow_acdc as pyf

def case39acdc_OPF():

    grid,res = pyf.cases['case39_acdc']()

    model, model_res , timing_info, solver_stats=pyf.Optimal_PF(grid,ObjRule={'Energy_cost': 1})

    res.All()
    
    model.display()
    
    model.obj.display()
    model.obj.pprint()
    print(timing_info)
    #model.PGi_gen.display()
def run_test():
    """Test case39 AC/DC optimal power flow."""
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    
    case39acdc_OPF()

if __name__ == "__main__":
    run_test()
