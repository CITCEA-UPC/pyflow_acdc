import pyflow_acdc as pyf

def folium_test():

        grid,res = pyf.cases['NS_MTDC']()

        pyf.Optimal_PF(grid)

        pyf.plot_folium(grid)

        print('folium test completed')

def run_test():
    """Test folium mapping functionality."""
    try:
        import folium
    except ImportError:
        print("folium is not installed...")
        return
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    
    folium_test()
if __name__ == "__main__":
    run_test()
    