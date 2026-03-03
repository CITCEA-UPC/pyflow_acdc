import networkx as nx
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import logging
import itertools
import base64
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import os
import utm
from shapely.geometry import Point, LineString,Polygon,MultiPolygon

from .Classes import Node_AC


def _loading_colormap(value, vmin=0, vmax=100):
    """
    Map a value to a color (green -> yellow -> red) for loading visualization.
    Replaces branca.colormap.LinearColormap.
    """
    # Clamp value to range
    normalized = max(0, min(1, (value - vmin) / (vmax - vmin)))
    
    # Create colormap: green (0) -> yellow (0.5) -> red (1)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'loading', ['green', 'yellow', 'red']
    )
    rgba = cmap(normalized)
    # Return as hex color string
    return mcolors.to_hex(rgba)


__all__ = ['plot_Graph',
           'Time_series_prob',
           'plot_neighbour_graph',
           'plot_TS_res',
           'plot_model_feasebility',
           'save_network_svg',
           'plot_3D']

def update_ACnode_hovertext(node,S_base,text):
    # print(f"Updating hover text for node: {node.name}")
    dec= 2
    if text =='data':
        name = node.name
        typ = node.type
        Load = np.round(node.PLi, decimals=dec)
        x_cord = node.x_coord
        y_cord = node.y_coord
        PZ = node.PZ
        node.hover_text = f"Node: {name}<br>coord: {x_cord},{y_cord}<br>Type: {typ}<br>Load: {Load}<br>Area: {PZ}"

    elif text=='inPu':
            name = node.name
            V = np.round(node.V, decimals=dec)
            theta = np.round(node.theta, decimals=dec)
            PGi= node.PGi+node.PGi_ren*node.curtailment +node.PGi_opt
            Gen =  np.round(PGi, decimals=dec)
            Load = np.round(node.PLi, decimals=dec)
            conv = np.round(node.P_s, decimals=dec)
            PZ = node.PZ
            node.hover_text = f"Node: {name}<br>Voltage: {V}<br>Angle: {theta}<br>Generation: {Gen}<br>Load: {Load}<br>Converters: {conv}<br>PZ: {PZ}"
    else:
            name = node.name
            V = int(np.round(node.V*node.kV_base, decimals=0))
            theta = int(np.round(np.degrees(node.theta), decimals=0))
            PGi= node.PGi+node.PGi_ren*node.curtailment  +node.PGi_opt
            Gen =  int(np.round(PGi*S_base, decimals=0))
            Load = int(np.round(node.PLi*S_base, decimals=0))
            conv = int(np.round(node.P_s*S_base, decimals=0))
            PZ = node.PZ
            node.hover_text = f"Node: {name}<br>Voltage: {V}kV<br>Angle: {theta}°<br>Generation: {Gen}MW<br>Load: {Load}MW<br>Converters: {conv}MW<br>PZ: {PZ}"
                
                    
def update_DCnode_hovertext(node,S_base,text):            
    dec= 2
    if text =='data':
        name = node.name
        typ = node.type
        Load = np.round(node.PLi, decimals=dec)
        x_cord = node.x_coord
        y_cord = node.y_coord
        PZ = node.PZ
        node.hover_text = f"Node: {name}<br>coord: {x_cord},{y_cord}<br>Type: {typ}<br>Load: {Load}<br>Area: {PZ}"

    elif text=='inPu':   
            name = node.name
            V = np.round(node.V, decimals=dec)
            conv  = np.round(node.Pconv, decimals=dec)
            node.hover_text = f"Node: {name}<br>Voltage: {V}<br><br>Converter: {conv}"
           
        
    else:
        name = node.name
        V = np.round(node.V*node.kV_base, decimals=0).astype(int)
        
        if node.ConvInv and node.Nconv >= 0.00001:
            conv  = np.round(node.Pconv*S_base, decimals=0).astype(int)
            nconv = np.round(node.Nconv,decimals=2)
            load = abs(int(np.round(conv / (node.conv_MW*nconv) * 100)))
            node.hover_text = f"Node: {name}<br>Voltage: {V}kV<br>Converter:{conv}MW<br>Number Converter: {nconv}<br>Converters loading: {load}%"
        else:
            node.hover_text = f"Node: {name}<br>Voltage: {V}kV"
     
            
            
def update_lineAC_hovertext(line,S_base,text):
    dec=2
    line.direction = 'from' if line.fromS >= 0 else 'to'
    if text =='data':
        name = line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        l = int(line.Length_km)
        z= np.round(line.Z,decimals=5)
        y= np.round(line.Y,decimals=5)
        rating = line.MVA_rating
        rating = np.round(rating,decimals=0)
        Line_tf = 'Transformer' if line.isTf else 'Line'
        cable = line.Cable_type
        line.hover_text = f"{Line_tf}: {name}<br> Z:{z}<br>Y:{y}<br>Length: {l}km<br>Rating: {rating}MVA<br>Type: {cable}"

    elif text=='inPu':
        
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS, decimals=dec)
        Sto = np.round(line.toS, decimals=dec)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=dec)
        Line_tf = 'Transformer' if line.isTf else 'Line'
        cable = line.Cable_type
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        line.hover_text = f"{Line_tf}: {name}<br> {line_string}<br>S from: {Sfrom}<br>S to: {Sto}<br>Loading: {Loading}%<br>Type: {cable}"
    else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS*S_base, decimals=0)
        Sto = np.round(line.toS*S_base, decimals=0)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        Line_tf = 'Transformer' if line.isTf else 'Line'
        cable = line.Cable_type
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        line.hover_text = f"{Line_tf}: {name}<br>  {line_string}<br>S from: {Sfrom}MVA<br>S to: {Sto}MVA<br>Loading: {Loading}%<br>Type: {cable}%"
              
def update_lineDC_hovertext(line,S_base,text):            
    dec=2
    line.direction = 'from' if line.fromP >= 0 else 'to'
    if text =='data':
        name = line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        
        r= np.round(line.R,decimals=5)
        l = int(line.Length_km)
        rating = line.MW_rating
        rating = np.round(rating,decimals=0)
        line.hover_text = f"Line: {name}<br> R:{r}<br>Length:{l}km<br>Rating: {rating}MW"

    elif text=='inPu':
     
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Pfrom= np.round(line.fromP, decimals=dec)
        Pto = np.round(line.toP, decimals=dec)
        np_line = np.round(line.np_line, decimals=1)
        if np_line == 0:
            load = 0
        else:
            load = max(np.abs(Pfrom), np.abs(Pto))*S_base/(line.MW_rating*line.np_line)*100
        Loading = np.round(load, decimals=dec)
        if Pfrom > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        line.hover_text = f"Line: {name}<br>  {line_string}<br>P from: {Pfrom}<br>P to: {Pto}<br>Loading: {Loading}%"
            
    else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Pfrom= np.round(line.fromP*S_base, decimals=0).astype(int)
        Pto = np.round(line.toP*S_base, decimals=0).astype(int)
        np_line = np.round(line.np_line, decimals=1)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        
        if Pfrom > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        line.hover_text = f"Line: {name}<br>  {line_string}<br>P from: {Pfrom}MW<br>P to: {Pto}MW<br>Loading: {Loading}%<br>Number Lines: {np_line}"



def update_lineACexp_hovertext(line,S_base,text):        
    dec=2
    line.direction = 'from' if line.fromS >= 0 else 'to'
    if text =='data':
        name = line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        l = int(line.Length_km)
        z= np.round(line.Z,decimals=5)
        y= np.round(line.Y,decimals=5)
        rating = line.MVA_rating
        rating = np.round(rating,decimals=0)
        Line_tf = 'Transformer' if line.isTf else 'Line'
        line.hover_text = f"{Line_tf}: {name}<br> Z:{z}<br>Y:{y}<br>Length: {l}km<br>Rating: {rating}MVA"

    elif text=='inPu':
        
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS, decimals=dec)
        Sto = np.round(line.toS, decimals=dec)
        np_line = np.round(line.np_line, decimals=1)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)    
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Transformer' if line.isTf else 'Line'
        line.hover_text = f"{Line_tf}: {name}<br> {line_string}<br>S from: {Sfrom}<br>S to: {Sto}<br>Loading: {Loading}%<br>Lines: {np_line}"
    else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS*S_base, decimals=0)
        Sto = np.round(line.toS*S_base, decimals=0)
        np_line = np.round(line.np_line, decimals=1)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Transformer' if line.isTf else 'Line'
        line.hover_text = f"Line: {name}<br>  {line_string}<br>S from: {Sfrom}MVA<br>S to: {Sto}MVA<br>Loading: {Loading}%<br>Lines: {np_line}"

def update_lineACrec_hovertext(line,S_base,text):
    dec=2
    line.direction = 'from' if line.fromS >= 0 else 'to'
    if text =='data':
        name = line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        l = int(line.Length_km)
        z= np.round(line.Z,decimals=5) if not line.rec_branch else np.round(line.Z_new,decimals=5)
        y= np.round(line.Y,decimals=5) if not line.rec_branch else np.round(line.Y_new,decimals=5)
        rating = line.MVA_rating if not line.rec_branch else line.MVA_rating_new
        rating = np.round(rating,decimals=0)
        Line_tf = 'Reconductoring branch'
        line.hover_text = f"{Line_tf}: {name}<br> Z:{z}<br>Y:{y}<br>Length: {l}km<br>Rating: {rating}MVA"

    elif text=='inPu':
        
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS, decimals=dec)
        Sto = np.round(line.toS, decimals=dec)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)    
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Reconductoring branch'
        line.hover_text = f"{Line_tf}: {name}<br> {line_string}<br>S from: {Sfrom}<br>S to: {Sto}<br>Loading: {Loading}%<br>Reconductoring: {line.rec_branch}"
    else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS*S_base, decimals=0)
        Sto = np.round(line.toS*S_base, decimals=0)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Reconductoring branch'
        line.hover_text = f"Line: {name}<br>  {line_string}<br>S from: {Sfrom}MVA<br>S to: {Sto}MVA<br>Loading: {Loading}%<br>Reconductoring: {line.rec_branch}"

def update_lineACct_hovertext(line,S_base,text):
    dec=2
    line.direction = 'from' if np.real(line.fromS) >= 0 else 'to'
    active_config = line.active_config
    if active_config == -1:
        return
    if text =='data':
        name = line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        l = int(line.Length_km)
        z= np.round(line.Z,decimals=5)
        y= np.round(line.Y,decimals=5)
        rating = line.MVA_rating
        rating = np.round(rating,decimals=0)
        Line_tf = 'Cable type line'
        line.hover_text = f"{Line_tf}: {name}<br> Z:{z}<br>Y:{y}<br>Length: {l}km<br>Rating: {rating}MVA"

    elif text=='inPu':
        
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS, decimals=dec)
        Sto = np.round(line.toS, decimals=dec)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)    
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Cable type line'
        line.hover_text = f"{Line_tf}: {name}<br> {line_string}<br>S from: {Sfrom}<br>S to: {Sto}<br>Loading: {Loading}%<br>Cable type: {line._active_config}"
    else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS*S_base, decimals=0)
        Sto = np.round(line.toS*S_base, decimals=0)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        Line_tf = 'Cable type line'
        line.hover_text = f"Line: {name}<br>  {line_string}<br>S from: {Sfrom}MVA<br>S to: {Sto}MVA<br>Loading: {Loading}%<br>Cable type: {line._active_config}"



def update_tf_hovertext(line,S_base,text):            
     dec=2
     line.direction = 'from' if line.fromS >= 0 else 'to'
     if text =='data':
         name = line.name
         fromnode = line.fromNode.name
         tonode = line.toNode.name
         l = int(line.Length_km)
         z= np.round(line.Z,decimals=5)
         y= np.round(line.Y,decimals=5)
         rating = line.MVA_rating
         rating = np.round(rating,decimals=0)
         Line_tf = 'Transformer' if line.isTf else 'Line'
         line.hover_text = f"{Line_tf}: {name}<br> Z:{z}<br>Y:{y}<br>Length: {l}km<br>Rating: {rating}MVA"

     elif text=='inPu':
         
         name= line.name
         fromnode = line.fromNode.name
         tonode = line.toNode.name
         Sfrom= np.round(line.fromS, decimals=dec)
         Sto = np.round(line.toS, decimals=dec)
         load = max(line.loading,line.ts_max_loading)
         Loading = np.round(load, decimals=dec)
         if np.real(Sfrom) > 0:
             line_string = f"{fromnode} -> {tonode}"
         else:
             line_string = f"{fromnode} <- {tonode}"
         line.hover_text = f"Transformer: {name}<br> {line_string}<br>S from: {Sfrom}<br>S to: {Sto}<br>Loading: {Loading}%"
     else:
        name= line.name
        fromnode = line.fromNode.name
        tonode = line.toNode.name
        Sfrom= np.round(line.fromS*S_base, decimals=0)
        Sto = np.round(line.toS*S_base, decimals=0)
        load = max(line.loading,line.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        if np.real(Sfrom) > 0:
            line_string = f"{fromnode} -> {tonode}"
        else:
            line_string = f"{fromnode} <- {tonode}"
        line.hover_text = f"Transformer: {name}<br>  {line_string}<br>S from: {Sfrom}MVA<br>S to: {Sto}MVA<br>Loading: {Loading}%"
  
def update_conv_hovertext(conv,S_base,text):            
     if text =='data':
         name= conv.name
         fromnode = conv.Node_DC.name
         tonode = conv.Node_AC.name
         rating = conv.MVA_max
         rating = np.round(rating,decimals=0)
         conv.hover_text = f"Converter: {name}<br>DC node: {fromnode}<br>AC node: {tonode}<br>Rating: {rating}"    
         
     elif text=='inPu':
         name= conv.name
         fromnode = conv.Node_DC.name
         tonode = conv.Node_AC.name
         Sfrom= np.round(conv.P_DC, decimals=0)
         Sto = np.round(np.sqrt(conv.P_AC**2 + conv.Q_AC**2) * np.sign(conv.P_AC), decimals=0)
         load = max(conv.loading,conv.ts_max_loading)
         Loading = np.round(load, decimals=0).astype(int)
         if np.real(Sfrom) > 0:
             conv_string = f"{fromnode} -> {tonode}"
         else:
             conv_string = f"{fromnode} <- {tonode}"
         conv.hover_text = f"Converter: {name}<br>  {conv_string}<br>P DC: {Sfrom}<br>S AC: {Sto}<br>Loading: {Loading}%"    
         
     else:    
        name= conv.name
        fromnode = conv.Node_DC.name
        tonode = conv.Node_AC.name
        Sfrom= np.round(conv.P_DC*S_base, decimals=0)
        Sto = np.round(np.sqrt(conv.P_AC**2+conv.Q_AC**2)*S_base*(conv.P_AC/np.abs(conv.P_AC)), decimals=0)
        load = max(conv.loading,conv.ts_max_loading)
        Loading = np.round(load, decimals=0).astype(int)
        if np.real(Sfrom) > 0:
            conv_string = f"{fromnode} -> {tonode}"
        else:
            conv_string = f"{fromnode} <- {tonode}"
        conv.hover_text = f"Converter: {name}<br>  {conv_string}<br>P DC: {Sfrom}MVA<br>S AC: {Sto}MVA<br>Loading: {Loading}%"    
        
def update_gen_hovertext(gen,S_base,text):            
     if text =='data':
         name= gen.name
         node = gen.Node_AC 
         n_gens = gen.np_gen
         installation_cost = gen.base_cost
         P_max = gen.Max_pow_gen * S_base * gen.np_gen
         P_min = gen.Min_pow_gen * S_base * gen.np_gen
         Q_max = gen.Max_pow_genR * S_base * gen.np_gen
         Q_min = gen.Min_pow_genR * S_base * gen.np_gen
         rating = gen.capacity_MVA
         rating = np.round(rating,decimals=1)
         
         gen.hover_text = f"Generator: {name}<br>Number of generators: {n_gens}<br>Rating: {rating}MVA<br>Installation cost: {installation_cost}<br>Fuel: {gen.gen_type}<br>P max: {P_max}MW<br>Q max: {Q_max}MVAR<br>P min: {P_min}MW<br>Q min: {Q_min}MVAR"    
         
     elif text =='inPu':
         name= gen.name
         n_gens = gen.np_gen
         Pto = np.round(gen.PGen, decimals=2)
         Qto = np.round(gen.QGen, decimals=2)
         load = gen.loading
         Loading = np.round(load, decimals=0).astype(int)
         
         gen.hover_text = f"Generator: {name}<br>Number of generators: {n_gens}<br> P gen: {Pto}<br>Q Gen: {Qto}<br>Loading: {Loading}%"   
     else:
        name= gen.name
        n_gens = gen.np_gen
        Pto = np.round(gen.PGen*S_base, decimals=1)
        Qto = np.round(gen.QGen*S_base, decimals=1)
        load = gen.loading
        Loading = np.round(load, decimals=0).astype(int)
        
        gen.hover_text = f"Generator: {name}<br>Number of generators: {n_gens}<br> P gen: {Pto*S_base}MW<br>Q Gen: {Qto*S_base}MVAR<br>Loading: {Loading}%"    
        
def update_renSource_hovertext(renSource,S_base,text):            
     if text =='data':
         name= renSource.name
         node = renSource.Node
         n_rs = renSource.np_rsgen
         installation_cost = renSource.base_cost
         rating = renSource.capacity_MVA
         Pmin = renSource.PGi_ren_base*renSource.min_gamma*renSource.np_rsgen*S_base
         Pmax = renSource.PGi_ren_base*renSource.np_rsgen*S_base
         rating = np.round(rating,decimals=0)
         renSource.hover_text = f"Ren Source: {name}<br>Number of sources: {n_rs}<br>Rating: {rating}<br>Installation cost: {installation_cost}<br>Tech: {renSource.rs_type}<br>P min: {Pmin}MW<br>P max: {Pmax}MW"    
         
     elif text=='inPu':
         name= renSource.name
         n_rs = renSource.np_rsgen
         Pto= np.round(renSource.PGi_ren, decimals=0)
         Curt = np.round((1-renSource.gamma)*100, decimals=0)
         renSource.hover_text = f"Ren Source: {name}<br>Number of sources: {n_rs}<br>  P : {Pto}<br>Curtailment: {Curt}%"    
     else:
         
        name= renSource.name
        n_rs = renSource.np_rsgen
        Pto= np.round(renSource.PGi_ren*S_base, decimals=0)
        Curt = np.round((1-renSource.gamma)*100, decimals=0)
        renSource.hover_text = f"Ren Source: {name}<br>Number of sources: {n_rs}<br>  P : {Pto}MW<br>Curtailment: {Curt}%"    
        
    
                            
                            
                             
def update_hovertexts(grid,text):
    S_base= grid.S_base        
    with ThreadPoolExecutor() as executor:
        futures = []
        if grid.nodes_AC is not None:
            # Update hover texts for nodes
            for node in grid.nodes_AC:
                futures.append(executor.submit(update_ACnode_hovertext, node, S_base, text))
        if grid.nodes_DC is not None:
            for node in grid.nodes_DC:
                futures.append(executor.submit(update_DCnode_hovertext, node, S_base, text))
        if grid.lines_AC is not None:
            # Update hover texts for lines
            for line in grid.lines_AC:
                futures.append(executor.submit(update_lineAC_hovertext, line, S_base, text))
        if grid.lines_DC is not None:
            for line in grid.lines_DC:
                futures.append(executor.submit(update_lineDC_hovertext, line, S_base, text))
        if grid.lines_AC_exp is not None:    
            for line in grid.lines_AC_exp:
                futures.append(executor.submit(update_lineACexp_hovertext, line, S_base, text))
        if grid.lines_AC_rec is not None:
            for line in grid.lines_AC_rec:
                futures.append(executor.submit(update_lineACrec_hovertext, line, S_base, text))
        if grid.lines_AC_ct is not None:
            for line in grid.lines_AC_ct:
                futures.append(executor.submit(update_lineACct_hovertext, line, S_base, text))
        if grid.lines_AC_tf is not None:    
            for line in grid.lines_AC_tf:
                futures.append(executor.submit(update_tf_hovertext, line, S_base, text))
        if grid.Converters_ACDC is not None:    
            for conv in grid.Converters_ACDC:
                futures.append(executor.submit(update_conv_hovertext, conv, S_base, text))
        if grid.Generators is not None:    
            for gen in grid.Generators:
                futures.append(executor.submit(update_gen_hovertext, gen, S_base, text))
        if grid.RenSources is not None:    
            for renSource in grid.RenSources:
                futures.append(executor.submit(update_renSource_hovertext, renSource, S_base, text))        

        # Wait for all futures to complete
        for future in futures:
            try:
                future.result()  # This will block until the task is finished
            except Exception as e:
                print(f"Error in thread: {e}")
        
            
def initialize_positions(Grid):
    """Initialize positions for the grid nodes."""
    return Grid.node_positions if Grid.node_positions is not None else {}

def assign_layout_to_missing_nodes(G, pos):
    """Assign layout to nodes missing positions."""
    missing_nodes = [
        node for node in G.nodes if node not in pos or pos[node][0] is None or pos[node][1] is None]
    if missing_nodes:
        try:
            # Attempt to apply planar layout to missing nodes
            pos_missing = nx.planar_layout(G.subgraph(missing_nodes))
            pos.update(pos_missing)
        except nx.NetworkXException as e:
            logging.warning("Planar layout failed, falling back to Kamada-Kawai layout.")
            # Fall back to Kamada-Kawai layout
            pos_missing = nx.kamada_kawai_layout(G.subgraph(missing_nodes))
            pos.update(pos_missing)
    return pos

def assign_converter_positions(Grid, pos):
    """Assign positions for DC nodes using corresponding AC node positions."""
    if Grid.Converters_ACDC is not None:
        for conv in Grid.Converters_ACDC:
            dc_node = conv.Node_DC
            ac_node = conv.Node_AC
            if ac_node in pos:
                pos[dc_node] = pos[ac_node]
            else:
                logging.warning(f"AC node {ac_node} for converter {conv.name} is missing in positions.")
    return pos

def calculate_positions(G, Grid):
    """Calculate positions for nodes in the graph."""
    # Step 1: Initialize positions
    pos = initialize_positions(Grid)
    
    # Step 2: Assign layout to missing nodes
    pos = assign_layout_to_missing_nodes(G, pos)
    
    # Step 3: Assign positions for converters
    pos = assign_converter_positions(Grid, pos)
    
    return pos


def plot_neighbour_graph(grid,node=None,node_name=None,base_node_size=10, proximity=1):
    G = grid.Graph_toPlot
    if node is not None:
        Gn = nx.ego_graph(G,node,proximity)
    elif node_name is not None:
        node= next((node for node in grid.nodes_AC if node.name == node_name), None)
        Gn = nx.ego_graph(G,node,proximity)
    if node is None: 
        print('Node name provided not found')
        return
    plot_Graph(grid,base_node_size=base_node_size,G=Gn)

        
def plot_Graph(Grid,text='inPu',base_node_size=10,G=None):
    
    if G is None:
        G = Grid.Graph_toPlot
    
    update_hovertexts(Grid, text) 
    
    # Initialize pos with node_positions if provided, else empty dict
    pos = calculate_positions(G, Grid)
 
    lines_ac = Grid.lines_AC if Grid.lines_AC is not None else []
    lines_ac_exp = Grid.lines_AC_exp if Grid.lines_AC_exp is not None else []
    lines_ac_rec = Grid.lines_AC_rec if Grid.lines_AC_rec is not None else []
    lines_ac_ct = Grid.lines_AC_ct if Grid.lines_AC_ct is not None else []
    lines_dc = Grid.lines_DC if Grid.lines_DC is not None else []
    nodes_DC = Grid.nodes_DC if Grid.nodes_DC is not None else []
    lines_dc_set = set(lines_dc)
    lines_ac_exp_set = set(lines_ac_exp)
    lines_ac_rec_set = set(lines_ac_rec)
    lines_ac_ct_set = set(lines_ac_ct)


    pio.renderers.default = 'browser'
    # Define a color palette for the subgraphs
    color_palette = itertools.cycle([
    'red', 'blue', 'green', 'purple', 'orange', 
    'cyan', 'magenta', 'brown', 'gray', 
    'black', 'lime', 'navy', 'teal',
    'violet', 'indigo', 'turquoise', 'beige', 'coral', 'salmon', 'olive'])
    # 
    # Find connected components (subgraphs)
    connected_components = list(nx.connected_components(G))
    
    
    pos_cache = pos
    node_traces_data = []
    edge_traces_data = []
    mnode_x_data = []
    mnode_y_data = []
    mnode_txt_data = []

    # Create traces for each subgraph with a unique color
    edge_traces = []
    node_traces = []
    mnode_trace = []
    
    
    for idx, subgraph_nodes in enumerate(connected_components):
        color = next(color_palette)
        
        # Create edge trace for the current subgraph
        for edge in G.subgraph(subgraph_nodes).edges(data=True):
            line = edge[2]['line']
            
            # Skip lines with np_line == 0
            if (line in lines_dc_set and line.np_line == 0) or (line in lines_ac_exp_set and line.np_line == 0):
                continue  # Skip plotting for lines where np_line == 0

            # Set line width based on line type
            if line in lines_dc_set:
                line_width = line.np_line if line.np_line > 0 else 0
            elif line in lines_ac_exp_set:
                line_width = line.np_line if line.np_line > 0 else 0
            else:
                line_width = 1
            
            # Cache positions to avoid repeated access
            x0, y0 = pos_cache[edge[0]]
            x1, y1 = pos_cache[edge[1]]
            
            # Collect midpoint data for marker
            mnode_x_data.append((x0 + x1) / 2)
            mnode_y_data.append((y0 + y1) / 2)
            mnode_txt_data.append(line.hover_text)
            
            
            # Append edge trace data
            edge_traces_data.append((x0, y0, x1, y1, line_width, color))
        
        # Process nodes for the current subgraph
        x_subgraph_nodes = []
        y_subgraph_nodes = []
        hover_texts_nodes_sub = []
        node_sizes = []
        node_opacities = []
        
        for node in subgraph_nodes:
            x_subgraph_nodes.append(pos_cache[node][0])
            y_subgraph_nodes.append(pos_cache[node][1])
            
            # Adjust for DC nodes
            
            if node in nodes_DC:
              if Grid.TEP_run:  
                node_size = max(base_node_size * (node.Nconv - node.Nconv_i) + base_node_size, base_node_size)
                node_opacity = max(min(node.Nconv, 1.0),0) if node.ConvInv else 1.0
            else:
                node_size = base_node_size
                node_opacity = 1.0
            
            hover_texts_nodes_sub.append(node.hover_text)
            node_sizes.append(node_size)
            node_opacities.append(node_opacity)
        
        # Collect node trace data
        node_traces_data.append((x_subgraph_nodes, y_subgraph_nodes, node_sizes, node_opacities, hover_texts_nodes_sub, color))

    
    # After the loops, create all traces in bulk
    # Edge Traces
    for (x0, y0, x1, y1, line_width, color) in edge_traces_data:
        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=line_width, color=color),
            visible=True,
            text="hover_text_placeholder",  # Replace with actual hover text
            hoverinfo='text'
        ))

    # Node Traces
    for (x_subgraph_nodes, y_subgraph_nodes, node_sizes, node_opacities, hover_texts_nodes_sub, color) in node_traces_data:
        node_traces.append(go.Scatter(
            x=x_subgraph_nodes,
            y=y_subgraph_nodes,
            mode='markers',
            marker=dict(
                size=node_sizes,
                color=color,
                opacity=node_opacities,
                line=dict(width=2)
            ),
            text=hover_texts_nodes_sub,
            hoverinfo='text',
            visible=True
        ))

    # Create mnode_trace (midpoint node trace) only after processing edges
    mnode_trace = go.Scatter(
        x=mnode_x_data,
        y=mnode_y_data,
        mode="markers",
        showlegend=False,
        hovertemplate="%{hovertext}<extra></extra>",
        visible=True,
        hovertext=mnode_txt_data,
        marker=dict(
            opacity=0,
            size=10,
            color=color
        )
    )
    

    layout = go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=600,  # Set width
        height=600,
        # updatemenus=updatemenus
    )
    
    
    
    # Create figure
    fig = go.Figure(data=edge_traces + node_traces + [mnode_trace], layout=layout)
    
    
    # Display plot
    pio.show(fig)
    s=1
    return fig
 
def plot_TS_res(grid, start, end, plotting_choices=[],show=True,path=None,save_format=None):
    Plot = [
        'Power Generation by price zone'    ,
        'Power Generation by generator'    ,
        'Curtailment'    ,
        'Market Prices'    ,
        'AC line loading'    ,
        'DC line loading'    ,
        'ACDC Converters'    ,
        'Power Generation by generator area chart'    ,
        'Power Generation by price zone area chart'    ,
    ]
    
    if plotting_choices == []:
        plotting_choices = Plot
    for plotting_choice in plotting_choices:
        # Verify that the choice is valid
        if plotting_choice not in Plot:
            print(f"Invalid plotting option: {plotting_choice}")
            continue

        
        # Retrieve the time series data for curtailment
        y_label = None
        ylim = None
        if plotting_choice == 'Curtailment':
            df = grid.time_series_results['curtailment'].loc[start:end]*100
            y_label = 'Curtailment (%)'
            ylim = [0,110]
        elif plotting_choice in ['Power Generation by generator','Power Generation by generator area chart']:
            df = grid.time_series_results['real_power_opf'].loc[start:end]*grid.S_base
            y_label = 'Power Generation (MW)'
        elif plotting_choice in ['Power Generation by price zone','Power Generation by price zone area chart'] :
            df = grid.time_series_results['real_power_by_zone'].loc[start:end] * grid.S_base
            y_label = 'Power Generation (MW)'
        elif plotting_choice == 'Market Prices':
            df = grid.time_series_results['prices_by_zone'].loc[start:end]
            df = df.loc[:, ~df.columns.str.startswith('o_')]
            y_label = 'Market Prices (€/MWh)'
        elif plotting_choice == 'AC line loading':
            df = grid.time_series_results['ac_line_loading'].loc[start:end]*100
            y_label = 'AC Line Loading (%)'
            ylim = [0,110]
        elif plotting_choice == 'DC line loading':
            df = grid.time_series_results['dc_line_loading'].loc[start:end]*100
            y_label = 'DC Line Loading (%)'
            ylim = [0,110]
        elif plotting_choice == 'ACDC Converters':
            df = grid.time_series_results['converter_loading'].loc[start:end] * grid.S_base
            y_label = 'ACDC Converters (MW)'
            ylim = [0,110]
        columns = df.columns  
        time = df.index  # Assuming the DataFrame index is time
       
        if show:
            # Show figure
            pio.renderers.default = 'browser'

            layout = dict(
                title=f"Time Series Plot: {plotting_choice}",  # Set title based on user choice
                hovermode="x"
            )

            cumulative_sum = None
            fig = go.Figure()
            # Check if we need to stack the areas for specific plotting choices
            stack_areas = plotting_choice in ['Power Generation by generator area chart', 'Power Generation by price zone area chart']

            # Adding traces to the subplots
            for col in columns:
                y_values = df[col]

                if stack_areas:
                    # print(stack_areas)
                    # If stacking, add the current values to the cumulative sum
                    if cumulative_sum is None:
                        cumulative_sum = y_values.copy()  # Start cumulative sum with the first selected row
                        fig.add_trace(
                            go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name', fill='tozeroy')
                        )
                    else:
                        y_values = cumulative_sum + y_values  # Stack current on top of cumulative sum
                        cumulative_sum = y_values  # Update cumulative sum
                        fig.add_trace(
                            go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name', fill='tonexty')
                        )
                else:
                    # Plot normally (no stacking)
                    fig.add_trace(
                        go.Scatter(x=time, y=y_values, name=col, hoverinfo='x+y+name')
                    )
            # Update layout
            fig.update_layout(layout)
            fig.show()

        if save_format is not None:
            # Convert 8.25 cm to inches and maintain ratio
            width_cm = 8.25
            ratio = 6/10  # Original height/width ratio
            width_inches = width_cm / 2.54
            height_inches = width_inches * ratio
            if len(df) > 10000:
                width_inches = width_inches * 2
            
            # Set publication-quality plotting parameters
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams.update({
                'figure.figsize': (width_inches, height_inches),
                'font.family': 'sans-serif',
                'font.size': 8,
                'axes.labelsize': 8,
                'axes.titlesize': 8,
                'xtick.labelsize': 7,
                'ytick.labelsize': 7,
                'legend.fontsize': 6,
                'lines.markersize': 4,
                'lines.linewidth': 1,
                'grid.alpha': 0.3
            })

            # Create figure with proper spacing for legend
            plt.figure(figsize=(width_inches, height_inches))
            
            # Adjust the plot area to make room for the legend
            plt.subplots_adjust(right=0.85)  # Make room for legend on the right

            max_colors = 8
            colors = plt.cm.Set2(np.linspace(0, 1, max_colors))
            line_markers = ['-', '--', ':', '-.']
            i = 0

            stack_areas = plotting_choice in ['Power Generation by generator area chart', 'Power Generation by price zone area chart']
            cumulative_sum = 0*df[columns[0]]
            for col in columns:
                y_values = df[col]
                current_line = '-' if i < max_colors else line_markers[((i - max_colors) % len(line_markers))]
                if stack_areas:
                    y_values = cumulative_sum + y_values
                    cumulative_sum = y_values
                    plt.plot(time, y_values, color=colors[i % max_colors], linestyle=current_line, label=col)
                else:
                    plt.plot(time, y_values, color=colors[i % max_colors], linestyle=current_line, label=col)
                i += 1

            plt.title(plotting_choice)
            plt.xlabel('Time')
            plt.xlim(time[0], time[-1])
            if ylim is not None:
                plt.ylim(ylim)
            plt.ylabel(y_label)

            # Adjust legend position based on number of items
            if i < 14:
                plt.legend(loc='center left', bbox_to_anchor=(1.02, 0.5),
                          frameon=False,
                          ncol=1)
            
            # Make x-axis labels horizontal
            plt.xticks(rotation=0)
            
            # Ensure everything fits
            plt.tight_layout()

            # Save with extra width to accommodate legend
            if path is None:
                plt.savefig(f"{plotting_choice}.{save_format}", 
                            bbox_inches='tight',  # Always use tight to include legend
                            dpi=300)
            else:
                plt.savefig(f"{path}/{plotting_choice}.{save_format}", 
                            bbox_inches='tight',
                            dpi=300)
            
            plt.close()
        

def Time_series_prob(grid, element_name, save_format=None, path=None):
        
        a = grid.Time_series
        
        df_gen = grid.time_series_results['real_power_opf']
        df_prices = grid.time_series_results['prices_by_zone']
        df_AC_line_res = grid.time_series_results['ac_line_loading']
        df_DC_line_res = grid.time_series_results['dc_line_loading']
        df_conv_res = grid.time_series_results['converter_loading']
  
        merged_df = pd.concat([df_gen, df_prices, df_AC_line_res, df_DC_line_res, df_conv_res], axis=1)


        width_cm = 8  # Doubled for side-by-side plots
        ratio = 6/10
        width_inches = width_cm / 2.54
        height_inches = width_inches * ratio

        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams.update({
            'figure.figsize': (width_inches, height_inches),
            'font.family': 'sans-serif',
            'font.size': 8,
            'axes.labelsize': 8,
            'axes.titlesize': 8,
            'xtick.labelsize': 7,
            'ytick.labelsize': 7,
            'legend.fontsize': 6,
            'lines.markersize': 4,
            'lines.linewidth': 1,
            'grid.alpha': 0.3
        })

        found = False
        for ts in a:
             if ts.name == element_name:
                    data = ts.data
                    found = True
                    break
        if not found:
            for col in merged_df.columns:
                if col == element_name:
                    data = merged_df[col]
                    break

        fig, ax1 = plt.subplots()
                    
        # Plot histogram on primary y-axis
        ax1.hist(data, bins=100, density=True, alpha=0.5, color='b', label='PDF')
        ax1.set_xlabel(element_name)
        ax1.set_ylabel('Probability Density', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        
        # Create secondary y-axis and plot CDF
        ax2 = ax1.twinx()
        sorted_data = np.sort(data)
        cumulative_prob = np.linspace(0, 1, len(sorted_data))
        ax2.plot(sorted_data, cumulative_prob, color='r', label='CDF')
        ax2.set_ylabel('Cumulative Probability', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save before showing
        if save_format:
            if path is None:
                plt.savefig(f"{element_name}_distribution.{save_format}", 
                        bbox_inches='tight',
                        dpi=300)
            else:
                plt.savefig(f"{path}/{element_name}_distribution.{save_format}", 
                        bbox_inches='tight',
                        dpi=300)
        
        plt.show()
        plt.close()
        return    



def create_subgraph_color_dict(G):
    
    
    
    color_palette_0 = itertools.cycle([
     'violet', 'limegreen',  'salmon',
    'burlywood', 'pink', 'cyan'
    ])
    
    color_palette_1 = itertools.cycle([
     'darkviolet', 'green',  'red',
    'darkorange', 'hotpink', 'lightseagreen'
    ])
    
    color_palette_2 = itertools.cycle([
         'darkmagenta', 'darkolivegreen',  'brown',
        'darkgoldenrod', 'crimson', 'darkcyan'
    ])

    color_palette_3 = itertools.cycle([
     'orchid', 'lightgreen',  'navajowhite',
    'tan', 'lightpink', 'paleturquoise'
    ])
    
    # Get connected components (subgraphs) of the graph G
    connected_components = list(nx.connected_components(G))
    subgraph_color_dict = {'MV':{},'HV': {}, 'EHV': {}, 'UHV': {}}
    
    # Loop through the connected components and assign colors
    for idx, subgraph_nodes in enumerate(connected_components):
        subgraph_color_dict['MV'][idx] = next(color_palette_0) 
        subgraph_color_dict['HV'][idx] = next(color_palette_1) 
        subgraph_color_dict['EHV'][idx] = next(color_palette_2) 
        subgraph_color_dict['UHV'][idx] = next(color_palette_3) 
    return subgraph_color_dict



def create_geometries(grid):
    """
    Create geometries for all grid elements if they don't exist.
    First checks if nodes have x and y coordinates, if not uses calculate_positions.
    Then creates geometries for all elements (nodes, lines, converters).
    """
    # Step 1: Check if nodes have coordinates, if not create synthetic ones
    G = grid.Graph_toPlot
    pos = calculate_positions(G, grid)
    
    # Step 2: Create geometries for nodes
    for node in grid.nodes_AC + grid.nodes_DC:
        if not hasattr(node, 'geometry') or node.geometry is None:
            if node in pos:
                x, y = pos[node]
                node.geometry = Point(x, y)
                # Update coordinates if they were None
                if node.x_coord is None:
                    node.x_coord = x
                if node.y_coord is None:
                    node.y_coord = y
    
    # Step 3: Create geometries for AC lines
    for line in grid.lines_AC + grid.lines_AC_tf + grid.lines_AC_rec + grid.lines_AC_ct + grid.lines_AC_exp:
        if not hasattr(line, 'geometry') or line.geometry is None:
            if hasattr(line, 'fromNode') and hasattr(line, 'toNode'):
                from_node = line.fromNode
                to_node = line.toNode
                if from_node in pos and to_node in pos:
                    x1, y1 = pos[from_node]
                    x2, y2 = pos[to_node]
                    line.geometry = LineString([(x1, y1), (x2, y2)])
    
    # Step 4: Create geometries for DC lines
    for line in grid.lines_DC:
        if not hasattr(line, 'geometry') or line.geometry is None:
            if hasattr(line, 'fromNode') and hasattr(line, 'toNode'):
                from_node = line.fromNode
                to_node = line.toNode
                if from_node in pos and to_node in pos:
                    x1, y1 = pos[from_node]
                    x2, y2 = pos[to_node]
                    line.geometry = LineString([(x1, y1), (x2, y2)])
    
    # Step 5: Create geometries for converters
    for conv in grid.Converters_ACDC:
        if not hasattr(conv, 'geometry') or conv.geometry is None:
            if hasattr(conv, 'Node_AC') and hasattr(conv, 'Node_DC'):
                ac_node = conv.Node_AC
                dc_node = conv.Node_DC
                if ac_node in pos and dc_node in pos:
                    x1, y1 = pos[ac_node]
                    x2, y2 = pos[dc_node]
                    conv.geometry = LineString([(x1, y1), (x2, y2)])
    
    # Step 6: Create geometries for generators and renewable sources
    for gen in grid.Generators + grid.RenSources:
        if not hasattr(gen, 'geometry') or gen.geometry is None:
            if hasattr(gen, 'Node_AC'):
                node = gen.Node_AC
                if node in pos:
                    x, y = pos[node]
                    gen.geometry = Point(x, y)

def save_network_svg(grid, name='grid_network', width=1000, height=800, journal=True, legend=True, square_ratio=False,poly=None,linestrings=None,coloring=None, poly_size=None):
    """Save the network as SVG file
    
    Parameters:
    -----------
    square_ratio : bool
        If True, forces both x and y axes to have the same range (uses the largest range needed)
        so that one step in x equals one step in y in the coordinate space.
    poly_size : tuple or None
        If provided and poly is not None, specifies the target size (width, height) in pixels
        for the polygon. Everything else will be scaled to fit this polygon size.
        Format: (target_width, target_height) in pixels.
    """
    try:
        import svgwrite
        
        # Check if all elements have geometries, if not create them
        elements_without_geometry = []
        
        # Check nodes
        for node in grid.nodes_AC + grid.nodes_DC:
            if not hasattr(node, 'geometry') or node.geometry is None:
                elements_without_geometry.append(f"Node {node.name}")
        
        # Check lines
        for line in grid.lines_AC + grid.lines_AC_tf + grid.lines_DC + grid.lines_AC_rec + grid.lines_AC_ct + grid.lines_AC_exp:
            if not hasattr(line, 'geometry') or line.geometry is None:
                elements_without_geometry.append(f"Line {line.name}")
        
        # Check converters
        for conv in grid.Converters_ACDC:
            if not hasattr(conv, 'geometry') or conv.geometry is None:
                elements_without_geometry.append(f"Converter {conv.name}")
        
        # Check generators and renewable sources
        for gen in grid.Generators + grid.RenSources:
            if not hasattr(gen, 'geometry') or gen.geometry is None:
                elements_without_geometry.append(f"Generator/RenSource {gen.name}")
        
        # If any elements are missing geometries, create them
        if elements_without_geometry:
            print(f"Creating geometries for {len(elements_without_geometry)} elements without geometries...")
            create_geometries(grid)

        if journal:
            # Convert 88mm to pixels (assuming 96 DPI)
            width = int(88 * 96 / 25.4)  # 25.4mm = 1 inch
            # Maintain aspect ratio
            if square_ratio:
                height = width 
            else:
                height = int(width * 0.8)  # Using 0.8 as a common aspect ratio for journal figures

        print(f"Current working directory: {os.getcwd()}")
        print(f"Will save as: {os.path.abspath(f'{name}.svg')}")
        # Create SVG drawing
        dwg = svgwrite.Drawing(f"{name}.svg", size=(f'{width}px', f'{height}px'), profile='tiny')
        
        # Get all geometries and their bounds
        all_bounds = []
        
        # Add lines
        for line in grid.lines_AC + grid.lines_AC_tf + grid.lines_DC + grid.lines_AC_rec + grid.lines_AC_ct +grid.lines_AC_exp:
            if hasattr(line, 'geometry') and line.geometry:
                all_bounds.append(line.geometry.bounds)
                
        # Add nodes
        for node in grid.nodes_AC + grid.nodes_DC:
            if hasattr(node, 'geometry') and node.geometry:
                all_bounds.append(node.geometry.bounds)
                
        # Add generators and renewable sources
        for gen in grid.Generators + grid.RenSources:
            if hasattr(gen, 'geometry') and gen.geometry:
                all_bounds.append(gen.geometry.bounds)
        
        # Add polygon bounds if provided
        def _iter_polys(obj):
            if obj is None:
                return
            if isinstance(obj, Polygon):
                yield obj
            elif isinstance(obj, MultiPolygon):
                for poly in obj.geoms:
                    yield poly
            elif isinstance(obj, (list, tuple)):
                for o in obj:
                    yield from _iter_polys(o)  # Recursively handle nested structures

        # Calculate polygon bounds separately if poly_size is specified
        poly_bounds = None
        if poly is not None:
            poly_bounds_list = []
            for geom in _iter_polys(poly):
                bounds = geom.bounds
                poly_bounds_list.append(bounds)
                all_bounds.append(bounds)
            
            if poly_bounds_list:
                poly_bounds = (
                    min(bound[0] for bound in poly_bounds_list),
                    min(bound[1] for bound in poly_bounds_list),
                    max(bound[2] for bound in poly_bounds_list),
                    max(bound[3] for bound in poly_bounds_list)
                )
        
        
        # Calculate overall bounds
        if all_bounds:
            minx = min(bound[0] for bound in all_bounds)
            miny = min(bound[1] for bound in all_bounds)
            maxx = max(bound[2] for bound in all_bounds)
            maxy = max(bound[3] for bound in all_bounds)
        else:
            print("No geometries found to plot")
            return

        # Calculate scaling factors
        # If poly_size is specified, determine scale from polygon FIRST, then use for everything
        if poly_size is not None and poly_bounds is not None:
            target_poly_width, target_poly_height = poly_size
            poly_minx, poly_miny, poly_maxx, poly_maxy = poly_bounds
            
            poly_x_range = poly_maxx - poly_minx
            poly_y_range = poly_maxy - poly_miny
            
            if poly_x_range == 0 or poly_y_range == 0:
                print("Warning: Polygon has zero width or height, cannot scale")
                # Fall through to normal scaling
                poly_size = None
            else:
                # Calculate scale factors for polygon to fit target size
                # Use minimum to maintain uniform scaling (circles stay circular)
                scale_x_poly = target_poly_width / poly_x_range
                scale_y_poly = target_poly_height / poly_y_range
                scale = min(scale_x_poly, scale_y_poly)  # Uniform scale for everything
                
                padding = 25
                
                # Calculate the overall bounds in scaled coordinates
                overall_x_range = (maxx - minx) * scale
                overall_y_range = (maxy - miny) * scale
                
                # Adjust width and height to accommodate everything
                width = int(overall_x_range + 2 * padding)
                height = int(overall_y_range + 2 * padding)
                
                # Update the SVG drawing size
                dwg = svgwrite.Drawing(f"{name}.svg", size=(f'{width}px', f'{height}px'), profile='tiny')
        
        # If poly_size was not set or failed, use normal scaling logic
        if poly_size is None or poly_bounds is None:
            if square_ratio:
                padding = 10
                # For square ratio: make both axes have the same range
                x_range = maxx - minx
                y_range = maxy - miny
                max_range = max(x_range, y_range)
                
                # Expand the smaller dimension to match the larger one
                if x_range < max_range:
                    center_x = (minx + maxx) / 2
                    minx = center_x - max_range / 2
                    maxx = center_x + max_range / 2
                
                if y_range < max_range:
                    center_y = (miny + maxy) / 2
                    miny = center_y - max_range / 2
                    maxy = center_y + max_range / 2
                
                # Now both ranges are equal, so use the same scale for both axes
                available_width = width - 2*padding
                available_height = height - 2*padding
                scale = min(available_width, available_height) / max_range
            else:
                padding = 25  # pixels of padding
                # Original scaling logic
                scale_x = (width - 2*padding) / (maxx - minx)
                scale_y = (height - 2*padding) / (maxy - miny)
                scale = min(scale_x, scale_y)
        
        def transform_coords(x, y):
            """Transform coordinates to SVG space"""
            return (
                padding + (x - minx) * scale,
                height - (padding + (y - miny) * scale)  # Flip Y axis
            )
        
        _LOADING_MODES = {'loading', 'ts_max_loading', 'ts_avg_loading'}
        _is_custom_color = coloring is not None and coloring not in _LOADING_MODES

        cable_type_colors = {
            0: 'cyan', 
            1: 'magenta', 
            2: 'brown', 
            3: 'gray', 
            4: 'lime', 
            5: 'navy', 
            6: 'teal', 
            7: 'violet', 
            8: 'indigo', 
            9: 'turquoise', 
            10: 'beige', 
            11: 'coral', 
            12: 'salmon', 
            13: 'olive'
        }
    
     
        # Draw background polygon(s) if provided (behind lines/nodes)
                
        if poly is not None:
            for geom in _iter_polys(poly):
                if isinstance(geom, Polygon):
                    poly_list = [geom]
                elif isinstance(geom, MultiPolygon):
                    poly_list = list(geom.geoms)
                else:
                    poly_list = []
                for pg in poly_list:
                    rings = [list(pg.exterior.coords)] + [list(r.coords) for r in pg.interiors]
                    d = ""
                    for coords in rings:
                        pts = [transform_coords(x, y) for (x, y) in coords]
                        d += "M " + " L ".join(f"{x},{y}" for (x, y) in pts) + " Z "
                    dwg.add(dwg.path(
                        d=d,
                        fill='#ADD8E6',
                        stroke='#ADD8E6',
                        stroke_width=2,
                        fill_rule='evenodd',
                        fill_opacity=0.15
                    ))
                    
                    # Draw contour lines (exterior and interior rings)
                    for coords in rings:
                        pts = [transform_coords(x, y) for (x, y) in coords]
                        contour_d = "M " + " L ".join(f"{x},{y}" for (x, y) in pts) + " Z"
                        dwg.add(dwg.path(
                            d=contour_d,
                            fill='none',
                            stroke='blue',
                            stroke_width=1
                        ))
        # Draw LineStrings if provided
        if linestrings is not None:
            for linestring in linestrings:
                if hasattr(linestring, 'geometry') and linestring.geometry:
                    coords = list(linestring.geometry.coords)
                elif hasattr(linestring, 'coords'):
                    coords = list(linestring.coords)
                else:
                    continue
                    
                path_data = "M "
                for c in coords:
                    svg_x, svg_y = transform_coords(c[0], c[1])
                    path_data += f"{svg_x},{svg_y} L "
                path_data = path_data[:-2]
                dwg.add(dwg.path(d=path_data, stroke='black', stroke_width=2, fill='none'))

        # Draw AC lines
        for line in grid.lines_AC + grid.lines_AC_tf + grid.lines_AC_rec + grid.lines_AC_ct:
            if line in grid.lines_AC_ct and getattr(line, 'active_config', 0) < 0:
                continue
            if hasattr(line, 'geometry') and line.geometry:
                coords = list(line.geometry.coords)
                path_data = "M "
                for c in coords:
                    svg_x, svg_y = transform_coords(c[0], c[1])
                    path_data += f"{svg_x},{svg_y} L "
                path_data = path_data[:-2]  # Remove last "L "
                if _is_custom_color:
                    color = coloring
                elif coloring in _LOADING_MODES:
                    if coloring == 'ts_max_loading':
                        load_show  = line.ts_max_loading
                    elif coloring == 'ts_avg_loading':
                        load_show  = line.ts_avg_loading
                    else:
                        load_show  = line.loading
                    if int(load_show) > 100:
                        color = 'blue'
                    else:
                        color = _loading_colormap(load_show)
                        color, opacity = _svg_color_and_opacity(color)
                else:
                    if line in grid.lines_AC_rec and line.rec_branch:
                        color = "green"
                    elif line in grid.lines_AC_ct:
                        color = cable_type_colors.get(line.active_config, "black")  
                    else:
                        color = "red" if getattr(line, 'isTf', False) else "black"
                
                dwg.add(dwg.path(d=path_data, stroke=color, stroke_width=2, fill='none'))
        

        for line in grid.lines_AC_exp:
            if hasattr(line, 'geometry') and line.geometry:
                coords = list(line.geometry.coords)
                path_data = "M "
                for c in coords:
                    svg_x, svg_y = transform_coords(c[0], c[1])
                    path_data += f"{svg_x},{svg_y} L "
                path_data = path_data[:-2]
                if _is_custom_color:
                    color = coloring
                elif coloring == 'loading':
                    map_color = _loading_colormap(min(max(line.loading,line.ts_max_loading),100))
                    color, opacity = _svg_color_and_opacity(map_color)
                else:
                    if line.np_line - line.np_line_b > 0.001:
                        color = "orange"
                    else:
                        color = "black"

                # Ensure stroke width is a plain Python float (svgwrite validator
                # does not accept NumPy scalar types).
                stroke_width = float(2 * float(line.np_line))
                dwg.add(dwg.path(d=path_data, stroke=color, stroke_width=stroke_width, fill='none'))


        # Draw DC lines
        for line in grid.lines_DC:
            if hasattr(line, 'geometry') and line.geometry:
                coords = list(line.geometry.coords)
                path_data = "M "
                for c in coords:
                    svg_x, svg_y = transform_coords(c[0], c[1])
                    path_data += f"{svg_x},{svg_y} L "
                path_data = path_data[:-2]
                stroke_width = float(2 * float(line.np_line))
                dwg.add(dwg.path(d=path_data, stroke='blue', stroke_width=stroke_width, fill='none'))
        
        # Draw converters
        for conv in grid.Converters_ACDC:
            if hasattr(conv, 'geometry') and conv.geometry:
                coords = list(conv.geometry.coords)
                path_data = "M "
                for c in coords:
                    svg_x, svg_y = transform_coords(c[0], c[1])
                    path_data += f"{svg_x},{svg_y} L "
                path_data = path_data[:-2]
                stroke_width = float(2 * float(conv.np_conv))
                dwg.add(dwg.path(d=path_data, stroke='purple', stroke_width=stroke_width, fill='none'))
        
        # Draw nodes
        for node in grid.nodes_AC + grid.nodes_DC:
            if hasattr(node, 'geometry') and node.geometry:
                x, y = node.geometry.x, node.geometry.y
                svg_x, svg_y = transform_coords(x, y)
                color = "black" if isinstance(node, Node_AC) else "purple"
                dwg.add(dwg.circle(center=(svg_x, svg_y), r=1, 
                                 fill=color, stroke=color))
                
        if grid.nct_AC != 0 and hasattr(grid.lines_AC_ct[0], 'cable_types'):
            # Transform the legend position to be within the visible bounds
            legend_x, legend_y = transform_coords(minx, maxy)  # Use the top-left corner of the bounds
            legend_spacing = 20  # Space between legend items
            
            # Add legend title
            
            
            # Add legend items
            if legend:

                dwg.add(dwg.text("Cable Types", 
                            insert=(legend_x, legend_y - 10),
                            font_size=15,
                            font_family="NewComputerModernSans"))

                if grid.Cable_options[0].active_config is not None:
                # Only show cable types that are active (>0.9)
                    space = 0
                    for i, cable_type in enumerate(grid.lines_AC_ct[0].cable_types):
                        if grid.Cable_options[0].active_config[i] > 0.9:
                            space += 1
                            color = cable_type_colors.get(i, "black")
                            # Add colored line
                            dwg.add(dwg.line(start=(legend_x, legend_y + space * legend_spacing),
                                        end=(legend_x + 30, legend_y + space * legend_spacing),
                                        stroke=color,
                                        stroke_width=2))
                            # Add text
                            dwg.add(dwg.text(f"{grid.lines_AC_ct[0].cable_types[i]}",
                                            insert=(legend_x + 40, legend_y + space * legend_spacing + 5),
                                            font_size=12,
                                            font_family="NewComputerModernSans",
                                            fill=color))
                
                else:
                    
                    for i, cable_type in enumerate(grid.lines_AC_ct[0].cable_types):
                        color = cable_type_colors.get(i, "black")
                        # Add colored line
                        dwg.add(dwg.line(start=(legend_x, legend_y + i * legend_spacing),
                                    end=(legend_x + 30, legend_y + i * legend_spacing),
                                    stroke=color,
                                    stroke_width=2))
                        # Add text
                        dwg.add(dwg.text(f"{grid.lines_AC_ct[0].cable_types[i]}",
                                        insert=(legend_x + 40, legend_y + i * legend_spacing + 5),
                                        font_size=12,
                                        font_family="NewComputerModernSans",
                                        fill=color))
        
        # Save the SVG file
        dwg.save()
        print(f"Network saved as {name}.svg")
        
    except ImportError as e:
        print(f"Could not save SVG: {e}. Please install svgwrite package.")

    return


    
def plot_model_feasebility(solver_stats,sol='all', x_axis='time', y_axis= 'objective', normalize = False,show=True, save_path=None, width_mm=None):
    import matplotlib.pyplot as plt
    # Respect optional width in millimeters for journal-style figures
    fig = None
    if width_mm is not None:
        fig_w_in = width_mm / 25.4
        fig_h_in = fig_w_in  # square by default
        fig = plt.figure(figsize=(fig_w_in, fig_h_in))
    #feasible_solutions.append((time_sec, objective, iterations))
    if sol == 'all':
        # [time_sec, objective, cumulative_iterations, nlp_call_num, is_feasible]
        solutions = solver_stats['all_solutions']

        if normalize:
            # Only consider objectives that have feasible flag set to True
            feasible_objectives = [objective for _, objective, _, _, is_feasible in solutions if is_feasible]
            if feasible_objectives:
                min_objective = min(feasible_objectives)
            else:
                min_objective = min(objective for _, objective, _, _, _ in solutions)
            solutions = [ [time_sec, (objective/min_objective-1)*100, cumulative_iterations, nlp_call_num, is_feasible] for time_sec, objective, cumulative_iterations, nlp_call_num, is_feasible in solutions]
    

        if x_axis == 'time':
            x_data = [time_sec for time_sec, _, _, _, _ in solutions]
        elif x_axis == 'iterations':
            x_data = [cumulative_iterations for _, _, cumulative_iterations, _, _ in solutions]

        if y_axis == 'objective':
            y_axis = 'objective [%]' if normalize else 'objective'
            y_data = [objective for _, objective, _, _, _ in solutions]
        elif y_axis == 'iterations':
            y_data = [cumulative_iterations for _, _, cumulative_iterations, _, _ in solutions]

        # Separate feasible and non-feasible points
        feasible_x = []
        feasible_y = []
        regular_x = []
        regular_y = []
        
        for i, solution in enumerate(solutions):
            if solution[4]:  # is_feasible is True
                feasible_x.append(x_data[i])
                feasible_y.append(y_data[i])
                regular_x.append(x_data[i])
                regular_y.append(y_data[i])
            else:
                regular_x.append(x_data[i])
                regular_y.append(y_data[i])

        # Plot regular points in default color
        if regular_x:
            plt.plot(regular_x, regular_y, 'o-', color='blue', label='NLP Progress')
        
        # Plot feasible points in red
        if feasible_x:
            plt.plot(feasible_x, feasible_y, 'o', color='red', markersize=8, label='Feasible Solutions')
        
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.grid(True)
        plt.legend()
        if show:
            plt.show()
        if save_path is not None:
            plt.savefig(save_path, bbox_inches='tight')
        if not show and fig is not None:
            plt.close(fig)
        return

    else:
        # [time_sec, objective, iterations]
        solutions = solver_stats['feasible_solutions']

        if normalize:
            min_objective = min(objective for _, objective, _ in solutions)
            solutions = [ (time_sec, objective/min_objective, iterations) for time_sec, objective, iterations in solutions]

        if x_axis == 'time':
            x_data = [time_sec for time_sec, _, _ in solutions]
        elif x_axis == 'iterations':
            x_data = [iterations for _, _, iterations in solutions]

        if y_axis == 'objective':
            y_data = [objective for _, objective, _ in solutions]
        elif y_axis == 'iterations':
            y_data = [iterations for _, _, iterations in solutions]

        plt.plot(x_data, y_data, 'o-')
        plt.xlabel(x_axis)
        plt.ylabel(y_axis)
        plt.grid(True)
        if show:
            plt.show()
        if save_path is not None:
            plt.savefig(save_path, bbox_inches='tight')
        if not show and fig is not None:
            plt.close(fig)
        plt.close(fig)
        return


def plot_3D(grid, show=True, save_path=None, coloring='cable_type',
            line_width=6, node_size=6, title=None,
            show_unused=False, poly=None, coords_lonlat=False,
            elevation_grid=None, show_elevation_surface=True,
            show_elevation_points=False, elevation_opacity=0.35,
            elevation_colorscale='Viridis',
            show_verticals=1.0,
            dev_area=None):
    """Plot the grid network in 3D using plotly.

    When ``coords_lonlat=True`` (default), node positions and LineString
    geometries are assumed to be in lon/lat and are converted to local
    meters so that X, Y and Z (elevation) share the same unit.
    Set ``coords_lonlat=True`` when coordinates are in lon/lat.

    Parameters
    ----------
    grid : Grid object
        Must contain ``lines_AC_ct`` with 3D ``geometry`` (has_z=True).
    show : bool
        Whether to display the figure interactively in the browser.
    save_path : str or None
        If given, save the figure as an HTML file.
    coloring : str
        'cable_type' colours cables by ``active_config``;
        'loading' colours by cable loading percentage.
    line_width : float
        Width of cable traces.
    node_size : float
        Marker size for nodes.
    title : str or None
        Figure title.
    show_unused : bool
        If True, draw unused cables (active_config < 0) as thin grey lines.
    poly : shapely Polygon/MultiPolygon or list, optional
        Development area polygon(s) to draw on the z=0 plane.
    coords_lonlat : bool
        If True, convert lon/lat to local meters via equirectangular
        projection.  If False, assume X/Y are already in meters.
    elevation_grid : pandas.DataFrame or dict, optional
        Optional set of elevation points to plot as a surface/plane.
        Expected columns/keys: ``x``, ``y``, ``elevation``.
        Coordinates are assumed to be in the same system as the plot
        (if ``coords_lonlat=True``, pass lon/lat so they are converted too).
    show_elevation_surface : bool
        If True (default) and ``elevation_grid`` is provided, draw a triangulated
        surface (Mesh3d) colored by elevation.
    show_elevation_points : bool
        If True, also plot the elevation points as markers.
    elevation_opacity : float
        Opacity for the elevation surface.
    elevation_colorscale : str or list
        Plotly colorscale for the elevation surface/points.
    show_verticals : float
        Opacity of vertical cable segments from 0 (hidden) to 1 (fully visible).
    """
    cable_type_colors = [
        '#00BCD4', '#E91E63', '#795548', '#9E9E9E', '#8BC34A',
        '#3F51B5', '#009688', '#9C27B0', '#303F9F', '#00ACC1',
        '#F5F5DC', '#FF7043', '#EF9A9A', '#827717',
    ]

    fig = go.Figure()

    # -- Coordinate projection ------------------------------------------------
    if coords_lonlat:
        slack = next((n for n in grid.nodes_AC if getattr(n, 'type', '') == 'Slack'), grid.nodes_AC[0])
        origin_lon, origin_lat = slack.x_coord, slack.y_coord
        x0, y0, zone0, letter0 = utm.from_latlon(origin_lat, origin_lon)

        def _to_m(lon, lat):
            lon = np.asarray(lon, dtype=float)
            lat = np.asarray(lat, dtype=float)
            if lon.ndim == 0:
                x, y, _, _ = utm.from_latlon(float(lat), float(lon), zone0, letter0)
                return (x - x0, y - y0)
            xs, ys = np.empty_like(lon), np.empty_like(lat)
            for i in range(len(lon)):
                xi, yi, _, _ = utm.from_latlon(float(lat[i]), float(lon[i]), zone0, letter0)
                xs[i], ys[i] = xi - x0, yi - y0
            return (xs, ys)
    else:
        def _to_m(x, y):
            return (x, y)

    # -- Optional elevation surface / plane ----------------------------------
    if elevation_grid is not None:
        if isinstance(elevation_grid, pd.DataFrame):
            if coords_lonlat and 'lon' in elevation_grid.columns and 'lat' in elevation_grid.columns:
                ex = elevation_grid['lon'].to_numpy()
                ey = elevation_grid['lat'].to_numpy()
            else:
                ex = elevation_grid['x'].to_numpy()
                ey = elevation_grid['y'].to_numpy()
            ez = elevation_grid['elevation'].to_numpy()
        else:
            if coords_lonlat and 'lon' in elevation_grid and 'lat' in elevation_grid:
                ex = np.asarray(elevation_grid['lon'])
                ey = np.asarray(elevation_grid['lat'])
            else:
                ex = np.asarray(elevation_grid['x'])
                ey = np.asarray(elevation_grid['y'])
            ez = np.asarray(elevation_grid['elevation'])


        # Build prepared dev_area polygon for triangle filtering
        _dev_prepared = None
        if dev_area is not None:
            from shapely.ops import unary_union as _union
            from shapely.prepared import prep as _prep
            polys = []
            for p in (dev_area if isinstance(dev_area, (list, tuple)) else [dev_area]):
                if isinstance(p, MultiPolygon):
                    polys.extend(p.geoms)
                else:
                    polys.append(p)
            _dev_prepared = _prep(_union(polys))

        ex_m, ey_m = _to_m(ex, ey)

        ex_m = np.asarray(ex_m).ravel()
        ey_m = np.asarray(ey_m).ravel()
        ez = np.asarray(ez).ravel()

        if show_elevation_surface and len(ex_m) >= 3:
            import matplotlib.tri as mtri
            tri = mtri.Triangulation(ex_m, ey_m)
            tris = tri.triangles

            # Remove triangles whose centroid falls outside the dev_area
            if _dev_prepared is not None and tris is not None and len(tris) > 0:
                keep = np.ones(len(tris), dtype=bool)
                for t_idx in range(len(tris)):
                    i0, i1, i2 = tris[t_idx]
                    cx = (ex[i0] + ex[i1] + ex[i2]) / 3.0
                    cy = (ey[i0] + ey[i1] + ey[i2]) / 3.0
                    if not _dev_prepared.contains(Point(cx, cy)):
                        keep[t_idx] = False
                tris = tris[keep]

            if tris is not None and len(tris) > 0:
                fig.add_trace(go.Mesh3d(
                    x=ex_m, y=ey_m, z=ez,
                    i=tris[:, 0], j=tris[:, 1], k=tris[:, 2],
                    intensity=ez,
                    colorscale=elevation_colorscale,
                    opacity=float(elevation_opacity),
                    name='Elevation surface',
                    legendgroup='elevation',
                    showlegend=True,
                    showscale=False,
                    hoverinfo='skip',
                ))

        if show_elevation_points and len(ex_m) > 0:
            fig.add_trace(go.Scatter3d(
                x=ex_m, y=ey_m, z=ez,
                mode='markers',
                marker=dict(size=2, color=ez, colorscale=elevation_colorscale, opacity=0.9),
                name='Elevation points',
                legendgroup='elevation',
                showlegend=not show_elevation_surface,
                hoverinfo='skip',
            ))

    # -- Helper: extract 3D coords from LineString, convert to meters ---------
    def _line_coords(geometry):
        coords = list(geometry.coords)
        if geometry.has_z:
            result = [(*_to_m(c[0], c[1]), c[2]) for c in coords]
        else:
            result = [(*_to_m(c[0], c[1]), 0.0) for c in coords]
        xs, ys, zs = zip(*result)
        return list(xs), list(ys), list(zs)

    def _split_verticals(xs, ys, zs):
        """Split a cable into (seabed, leading_vertical, trailing_vertical).

        A vertical is detected where consecutive points share the same x,y.
        Returns (main_xs, main_ys, main_zs), (lead_xs, lead_ys, lead_zs), (trail_xs, trail_ys, trail_zs).
        Lead/trail lists are empty if no vertical exists.
        """
        n = len(xs)
        # Find end of leading vertical
        lead_end = 0
        while lead_end < n - 1 and xs[lead_end] == xs[lead_end + 1] and ys[lead_end] == ys[lead_end + 1]:
            lead_end += 1
        # Find start of trailing vertical
        trail_start = n - 1
        while trail_start > lead_end and xs[trail_start] == xs[trail_start - 1] and ys[trail_start] == ys[trail_start - 1]:
            trail_start -= 1

        lead = (xs[:lead_end + 1], ys[:lead_end + 1], zs[:lead_end + 1]) if lead_end > 0 else ([], [], [])
        trail = (xs[trail_start:], ys[trail_start:], zs[trail_start:]) if trail_start < n - 1 else ([], [], [])
        main = (xs[lead_end:trail_start + 1], ys[lead_end:trail_start + 1], zs[lead_end:trail_start + 1])
        return main, lead, trail

    # -- Draw cables ----------------------------------------------------------
    used_configs = set()
    for line in grid.lines_AC_ct:
        geo = getattr(line, 'geometry', None)
        if geo is None:
            continue
        
        is_used = getattr(line, 'active_config', 0) >= 0

        if not is_used and not show_unused:
            continue

        xs, ys, zs = _line_coords(geo)

        if not is_used:
            color = 'lightgrey'
            width = 1
            legend_group = 'unused'
            legend_name = 'Unused'
            show_legend = legend_group not in used_configs
            used_configs.add(legend_group)
        elif coloring == 'loading':
            load_val = getattr(line, 'loading', 0)
            color = _loading_colormap(min(load_val, 100))
            width = line_width
            legend_group = None
            legend_name = f'{line.name} ({load_val:.0f}%)'
            show_legend = True
        else:
            cfg = getattr(line, 'active_config', 0)
            color = cable_type_colors[cfg % len(cable_type_colors)]
            width = line_width
            legend_group = f'type_{cfg}'
            legend_name = f'Cable type {cfg}'
            show_legend = cfg not in used_configs
            used_configs.add(cfg)

        vertical_opacity = 1.0 if show_verticals is True else (0.0 if show_verticals is False else float(show_verticals))
        vertical_opacity = max(0.0, min(1.0, vertical_opacity))

        (mx, my, mz), (lx, ly, lz), (tx, ty, tz) = _split_verticals(xs, ys, zs)
        fig.add_trace(go.Scatter3d(
            x=mx, y=my, z=mz,
            mode='lines',
            line=dict(color=color, width=width),
            name=legend_name,
            legendgroup=legend_group,
            showlegend=show_legend,
            hovertext=f'{line.name}',
            hoverinfo='text',
        ))
        if vertical_opacity > 0:
            for vx, vy, vz in [(lx, ly, lz), (tx, ty, tz)]:
                if vx:
                    fig.add_trace(go.Scatter3d(
                        x=vx, y=vy, z=vz,
                        mode='lines',
                        line=dict(color=color, width=max(1, width // 2)),
                        opacity=vertical_opacity,
                        legendgroup=legend_group,
                        showlegend=False,
                        hoverinfo='skip',
                    ))

    # -- Draw export cables ---------------------------------------------------
    _exp_added = False
    for line in getattr(grid, 'lines_AC_exp', []):
        geo = getattr(line, 'geometry', None)
        if geo is None:
            continue
        xs, ys, zs = _line_coords(geo)
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs,
            mode='lines',
            line=dict(color='black', width=line_width + 1),
            name='Export cable',
            legendgroup='export',
            showlegend=not _exp_added,
            hovertext=f'{line.name}',
            hoverinfo='text',
        ))
        _exp_added = True

    # -- Build node elevation lookup from line endpoints -----------------------
    node_z_lookup = {}
    for line in grid.lines_AC_ct + getattr(grid, 'lines_AC_exp', []):
        geo = getattr(line, 'geometry', None)
        if geo is None or not getattr(geo, 'has_z', False):
            continue
       
        coords = list(geo.coords)
        if coords and len(coords[0]) >= 3:
            fn = getattr(line.fromNode, 'name', None)
            tn = getattr(line.toNode, 'name', None)
            start_z = coords[0][2]
            end_z = coords[-1][2]
            if fn is not None and fn not in node_z_lookup:
                node_z_lookup[fn] = start_z
            if tn is not None and tn not in node_z_lookup:
                node_z_lookup[tn] = end_z

    # -- Draw nodes -----------------------------------------------------------
    turbine_x, turbine_y, turbine_z, turbine_text = [], [], [], []
    sub_x, sub_y, sub_z, sub_text = [], [], [], []

    for node in grid.nodes_AC:
        ntype = getattr(node, 'type', '')
        mx, my = _to_m(node.x_coord, node.y_coord)
        z = node_z_lookup.get(node.name, 0.0)

        hover = f'{node.name}<br>({mx:.0f}, {my:.0f}, {z:.1f}) m'
        if ntype == 'Slack':
            sub_x.append(mx); sub_y.append(my); sub_z.append(z); sub_text.append(hover)
        else:
            turbine_x.append(mx); turbine_y.append(my); turbine_z.append(z); turbine_text.append(hover)

    if turbine_x:
        fig.add_trace(go.Scatter3d(
            x=turbine_x, y=turbine_y, z=turbine_z,
            mode='markers',
            marker=dict(size=node_size, color='green', symbol='circle'),
            name='Turbines',
            hovertext=turbine_text,
            hoverinfo='text',
        ))
    if sub_x:
        fig.add_trace(go.Scatter3d(
            x=sub_x, y=sub_y, z=sub_z,
            mode='markers',
            marker=dict(size=node_size * 2, color='red', symbol='diamond'),
            name='Substations',
            hovertext=sub_text,
            hoverinfo='text',
        ))

    # -- Draw development area polygon on z=0 plane ---------------------------
    if poly is not None:
        def _iter_polys(obj):
            if isinstance(obj, Polygon):
                yield obj
            elif isinstance(obj, MultiPolygon):
                for p in obj.geoms:
                    yield p
            elif isinstance(obj, (list, tuple)):
                for o in obj:
                    yield from _iter_polys(o)

        for pg in _iter_polys(poly):
            ring = list(pg.exterior.coords)
            pts = [_to_m(c[0], c[1]) for c in ring]
            px, py = zip(*pts)
            pz = [0.0] * len(px)
            fig.add_trace(go.Scatter3d(
                x=list(px), y=list(py), z=pz,
                mode='lines',
                line=dict(color='dodgerblue', width=2),
                name='Dev. area',
                legendgroup='dev_area',
                showlegend=True,
                hoverinfo='skip',
            ))

    # -- Layout ---------------------------------------------------------------
    fig.update_layout(
        title=title or 'Array Cable Layout – 3D',
        scene=dict(
            xaxis_title='X (meters)',
            yaxis_title='Y (meters)',
            zaxis_title='Elevation (meters)',
        ),
        width=900,
        height=800,
        template='plotly_white',
        legend=dict(
            itemsizing='constant',
            yanchor='top', y=0.99,
            xanchor='left', x=1.01,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    if save_path is not None:
        pio.write_html(fig, save_path)
        print(f"3D plot saved to {save_path}")

    if show:
        fig.show(renderer='browser')

    return fig


def _svg_color_and_opacity(color):
    # Return (svg_color, opacity_or_None)
    # Accepts '#RRGGBB', '#RRGGBBAA', (r,g,b), (r,g,b,a), 'rgba(r,g,b,a)'
    if isinstance(color, (list, tuple)):
        if len(color) == 4:
            r, g, b, a = color
            # handle 0..1 floats or 0..255 ints
            if max(r, g, b) <= 1:
                r, g, b = int(r*255), int(g*255), int(b*255)
            if a > 1:
                a = a/255.0
            return f"rgb({int(r)},{int(g)},{int(b)})", float(a)
        if len(color) == 3:
            r, g, b = color
            if max(r, g, b) <= 1:
                r, g, b = int(r*255), int(g*255), int(b*255)
            return f"rgb({int(r)},{int(g)},{int(b)})", None
    if isinstance(color, str):
        s = color.strip()
        if s.startswith('#') and len(s) == 9:  # #RRGGBBAA
            rgb = s[:7]
            a = int(s[7:9], 16) / 255.0
            return rgb, a
        if s.lower().startswith('rgba(') and s.endswith(')'):
            parts = [p.strip() for p in s[5:-1].split(',')]
            r, g, b = [int(float(x)) for x in parts[:3]]
            a = float(parts[3])
            return f"rgb({r},{g},{b})", a
    return color, None