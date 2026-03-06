import pyflow_acdc as pyf
from pathlib import Path

current_file = Path(__file__).resolve()
examples_path = current_file.parents[2] / "examples"

def barrow(ct=3, ns= None, nt = None,curtailment_allowed=0  ):
    touple = pyf.grid_creator.load_pickle(str(examples_path / "barrow.pkl.gz"))
    array_graph, Data, cable_types, final_polygon = touple
    
    if nt is not None:
        Data["turbine"] = Data["turbine"].assign(connections=3)
        
    if ns is not None:
        Data["offshore_substation"] = Data["offshore_substation"].assign(connections=ns)

    if ns is not None:
        Data["transformer_station"] = Data["transformer_station"].assign(connections=ns)


    grid, res = pyf.Create_grid_from_turbine_graph(
        array_graph, Data,
        cable_types=cable_types,
        cable_types_allowed=ct, 
        curtailment_allowed=curtailment_allowed,
        MIP_time=600,
        name='barrow'
    )
    return grid, res