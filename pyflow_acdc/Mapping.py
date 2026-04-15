import networkx as nx
import numpy as np
import os
from datetime import datetime, timedelta
from pathlib import Path
from importlib import resources
import colorsys

import geopandas as gpd
import pandas as pd
import folium
import branca
from folium.plugins import Draw,MarkerCluster,AntPath,TimestampedGeoJson
import webbrowser
from shapely.geometry import Point, LineString
from .Graph_and_plot import update_hovertexts, create_subgraph_color_dict
from .Classes import Node_AC

def darken_color(color, factor=0.6):
    """
    Darken a CSS color by reducing its brightness.
    
    Args:
        color: CSS color name (e.g., 'royalblue', 'black') or hex string
        factor: How much to darken (0.0 to 1.0). Lower = darker. Default 0.6.
    
    Returns:
        Hex color string (e.g., '#4a5a7f')
    """
    # Dictionary of common CSS color names to RGB
    css_colors = {
        'black': (0, 0, 0),
        'white': (1, 1, 1),
        'red': (1, 0, 0),
        'green': (0, 0.5, 0),
        'blue': (0, 0, 1),
        'yellow': (1, 1, 0),
        'cyan': (0, 1, 1),
        'magenta': (1, 0, 1),
        'orange': (1, 0.647, 0),
        'purple': (0.5, 0, 0.5),
        'brown': (0.647, 0.165, 0.165),
        'pink': (1, 0.753, 0.796),
        'gray': (0.5, 0.5, 0.5),
        'grey': (0.5, 0.5, 0.5),
        'darkblue': (0, 0, 0.545),
        'royalblue': (0.255, 0.412, 0.882),
        'teal': (0, 0.5, 0.5),
        'violet': (0.933, 0.510, 0.933),
        'indigo': (0.294, 0, 0.510),
        'turquoise': (0.251, 0.878, 0.816),
        'beige': (0.961, 0.961, 0.863),
        'coral': (1, 0.498, 0.314),
        'salmon': (0.980, 0.502, 0.447),
        'olive': (0.502, 0.502, 0),
        'lime': (0, 1, 0),
        'navy': (0, 0, 0.5),
        'limegreen': (0.196, 0.804, 0.196),
        'burlywood': (0.871, 0.722, 0.529),
        'darkviolet': (0.580, 0, 0.827),
        'hotpink': (1, 0.412, 0.706),
        'lightseagreen': (0.125, 0.698, 0.667),
        'darkmagenta': (0.545, 0, 0.545),
        'darkolivegreen': (0.333, 0.420, 0.184),
        'darkgoldenrod': (0.722, 0.525, 0.043),
        'crimson': (0.863, 0.078, 0.235),
        'darkcyan': (0, 0.545, 0.545),
        'orchid': (0.855, 0.439, 0.839),
        'lightgreen': (0.565, 0.933, 0.565),
        'navajowhite': (1, 0.871, 0.678),
        'tan': (0.824, 0.706, 0.549),
        'lightpink': (1, 0.714, 0.757),
        'paleturquoise': (0.686, 0.933, 0.933),
        'darkorange': (1, 0.549, 0)
    }
    
    # Get RGB value
    rgb = css_colors.get(color.lower(), (0.5, 0.5, 0.5))  # Default to gray if not found
    
    # Convert RGB to HSV (Hue, Saturation, Value)
    hsv = colorsys.rgb_to_hsv(rgb[0], rgb[1], rgb[2])
    
    # Reduce the Value (brightness) component
    new_v = max(0.0, hsv[2] * factor)  # Ensure we don't go negative
    
    # Convert back to RGB
    new_rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], new_v)
    
    # Convert to hex
    hex_color = '#{:02x}{:02x}{:02x}'.format(
        int(new_rgb[0] * 255),
        int(new_rgb[1] * 255),
        int(new_rgb[2] * 255)
    )
    
    return hex_color

def create_geometries_from_coords(grid):
    for node in grid.nodes_AC+grid.nodes_DC:
        if node.x_coord is not None and node.y_coord is not None and node.geometry is None:
            node.geometry = Point(node.x_coord, node.y_coord)
    for line in grid.lines_AC+grid.lines_DC +grid.lines_AC_tf+grid.lines_AC_rec+grid.lines_AC_ct+grid.lines_AC_exp:
        if line.fromNode.x_coord is not None and line.fromNode.y_coord is not None and line.toNode.x_coord is not None and line.toNode.y_coord is not None and line.geometry is None:
            line.geometry = LineString([(line.fromNode.x_coord, line.fromNode.y_coord),
                                        (line.toNode.x_coord, line.toNode.y_coord)])
    for conv in grid.Converters_ACDC:
        if conv.Node_AC.x_coord is not None and conv.Node_AC.y_coord is not None and conv.Node_DC.x_coord is not None and conv.Node_DC.y_coord is not None and conv.geometry is None:
            conv.geometry = LineString([(conv.Node_AC.x_coord, conv.Node_AC.y_coord),
                                        (conv.Node_DC.x_coord, conv.Node_DC.y_coord)])
    for gen in grid.Generators+grid.Generators_DC+grid.RenSources:
        if gen.x_coord is not None and gen.y_coord is not None and gen.geometry is None:
            gen.geometry = Point(gen.x_coord, gen.y_coord)



def plot_folium_network(
    grid,
    text='data',
    name=None,
    tiles="CartoDB Positron",
    polygon=None,
    linestrings=None,
    ant_path='None',
    clustering=True,
    coloring=None,
    show=True,
    planar=False,
    scale_gen=False,
    base_icon_size=24,
    plot_load=True,
    show_all=False,
    add_marine_regions_wms=False,
    line_size_factor=1.0,
):
    # "OpenStreetMap",     "CartoDB Positron"     "Cartodb dark_matter" 
    if name is None:
        name = grid.name
    update_hovertexts(grid, text) 

    create_geometries_from_coords(grid)
  
    
    G = grid.Graph_toPlot  # Assuming this is your main graph object
    subgraph_colors= create_subgraph_color_dict(G)
    subgraph_dict = {} 
    
    # Map each line to its subgraph index
    for idx, subgraph_nodes in enumerate(nx.connected_components(G)):
        for edge in G.subgraph(subgraph_nodes).edges(data=True):
            line = edge[2]['line']
            subgraph_dict[line] = idx
        for node in subgraph_nodes:    
            subgraph_dict[node] = idx
            connected_gens = getattr(node, 'connected_gen', [])  
            connected_renSources = getattr(node, 'connected_RenSource', [])  
            subgraph_dict.update({gen: idx for gen in connected_gens})
            subgraph_dict.update({rs:  idx for rs  in connected_renSources})
    
    # Extract line data (AC and HVDC) into a GeoDataFrame
    def extract_line_data(lines, line_type):
        line_data = []

        if line_type == 'DC': 
            subgraph_dc_counts = {}
            for line_obj in lines:
                subgraph_idx = subgraph_dict.get(line_obj)  # Avoid KeyError
                if subgraph_idx is not None:  # Ensure the line is in subgraph_dict
                    subgraph_dc_counts[subgraph_idx] = subgraph_dc_counts.get(subgraph_idx, 0) + 1
        
        if coloring == 'loss':
            min_loss = min(np.real(line.loss) for line in lines)
            max_loss = max(np.real(line.loss) for line in lines)
            if min_loss == max_loss:
                max_loss += 0.1 
            colormap = branca.colormap.LinearColormap(
                colors=["green", "yellow", "red"],
                vmin=min_loss, 
                vmax=max_loss
                )
        elif coloring in ['loading','ts_max_loading','ts_avg_loading']:
            colormap = branca.colormap.LinearColormap(
                colors=["green", "yellow", "red"],
                vmin=0, 
                vmax=100
                )
        elif coloring == 'Efficiency':
           colormap = branca.colormap.LinearColormap(
               colors=["red", "yellow","green"],
               vmin=70, 
               vmax=100
               )
        
        # test_values = [min_loss, (min_loss + max_loss) / 2, max_loss]
        # for val in test_values:
        #     print(f"Loss: {val}, Color: {colormap(val)}")
        for line_obj in lines:
            subgraph_idx = subgraph_dict.get(line_obj)
            geometry = getattr(line_obj, 'geometry', None)  # Ensure geometry exists
            VL = 'MV' if line_obj.toNode.kV_base < 110 else \
                 'HV' if line_obj.toNode.kV_base < 300 else \
                 'EHV' if line_obj.toNode.kV_base < 500 else \
                 'UHV'
                 
            line_type_indv= line_type    
            
            if line_type_indv == 'DC' and subgraph_dc_counts.get(subgraph_idx, 0) >= 2:
               line_type_indv = 'MTDC'
            
            
            area = line_obj.toNode.PZ if line_obj.toNode.PZ == line_obj.fromNode.PZ else 'ICL'
            ant_v = False
            
            if area == 'ICL' or line_type == 'DC':
                ant_v = True
            if ant_path == 'All' and VL != 'MV':
                ant_v = True

            thck= getattr(line_obj, 'np_line', 1)
            if coloring == 'loss':
                color = colormap(np.real(line_obj.loss))
                # print(f'{np.real(line.loss)} - {color}')
            elif coloring in ['loading','ts_max_loading','ts_avg_loading']:
                if coloring == 'ts_max_loading':
                    load_show  = line_obj.ts_max_loading
                elif coloring == 'ts_avg_loading':
                    load_show  = line_obj.ts_avg_loading
                else:
                    load_show  = line_obj.loading
                if int(load_show) > 100:
                    color = 'blue'
                else:
                    color = colormap(np.real(load_show))
                    
            elif coloring == 'Efficiency':
                loss =np.real(line_obj.loss)
                if line_type== 'DC':
                    power=max(np.abs(line_obj.fromP),np.abs(line_obj.toP))
                else:
                    power =max(np.abs(np.real(line_obj.fromS)),np.abs(np.real(line_obj.toS)))
                eff=(1-loss/power)*100 if power != 0 else 0
                color= colormap(eff)
                # print(f'{eff} - {color}')
            elif line_type == 'CSS':
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
                if line_obj.active_config != -1:
                    color= cable_type_colors[line_obj.active_config]
                else:
                    color= 'black'
                    thck= 0
            else:
                color=('black' if getattr(line_obj, 'isTf', False)  # Defaults to False if 'isTF' does not exist/
                        else subgraph_colors[VL].get(subgraph_idx, "black") if line_type == 'AC' or line_type == 'rec_AC' 
                        else 'darkblue' if line_type_indv == 'MTDC' 
                        else 'royalblue')
            if line_type == 'rec_AC' and line_obj.rec_branch:
                color = darken_color(color, factor=0.6) 
            if geometry and not geometry.is_empty:
                line_data.append({
                    "geometry": geometry,
                    "type": line_type_indv,
                    "name": getattr(line_obj, 'name', 'Unknown'),
                    "Direction": line_obj.direction,
                    "ant_viable": ant_v, 
                    "thck": thck,
                    "VL" :VL,
                    "area":area,
                    "tf": getattr(line_obj, 'isTf', False),
                    "hover_text": getattr(line_obj, 'hover_text', 'No info'),
                    "color":color
                })
        
        if lines:  # Using if lines instead of if lines != [] is more pythonic
            return gpd.GeoDataFrame(line_data, geometry="geometry")
        else:
            # Create an empty GeoDataFrame with the expected columns
            return gpd.GeoDataFrame(columns=['geometry', 'type', 'name', 'Direction', 'ant_viable', 
                                           'thck', 'VL', 'area', 'tf', 'hover_text', 'color'], 
                                  geometry='geometry')
   
   
    # Create GeoDataFrames for AC and HVDC lines
    gdf_lines_AC = extract_line_data(grid.lines_AC+grid.lines_AC_tf, "AC")
    if grid.lines_AC_exp != []:
        gdf_lines_AC_exp = extract_line_data(grid.lines_AC_exp, "exp_AC")
    else:
        gdf_lines_AC_exp = gpd.GeoDataFrame(columns=["geometry", "type", "name", "VL", "tf", "hover_text", "color"])

    if grid.lines_AC_rec != []:
        gdf_lines_AC_rec = extract_line_data(grid.lines_AC_rec, "rec_AC")
    else:
        gdf_lines_AC_rec = gpd.GeoDataFrame(columns=["geometry", "type", "name", "VL", "tf", "hover_text", "color"])
    if grid.lines_AC_ct != []:
        gdf_lines_AC_ct = extract_line_data(grid.lines_AC_ct, "CSS")
    else:
        gdf_lines_AC_ct = gpd.GeoDataFrame(columns=["geometry", "type", "name", "VL", "tf", "hover_text", "color"])
    
    def filter_vl_and_tf(gdf):
    # Filter lines based on Voltage Level (VL)
        AC_mv = gdf[gdf['VL'] == 'MV']    
        AC_hv = gdf[gdf['VL'] == 'HV']
        AC_ehv = gdf[gdf['VL'] == 'EHV']
        AC_uhv = gdf[gdf['VL'] == 'UHV']
    
        # Filter transformer lines (isTf == True)
        AC_tf = gdf[gdf['tf'] == True] if 'tf' in gdf.columns else None

        return AC_mv,AC_hv, AC_ehv, AC_uhv, AC_tf
   
    gdf_lines_AC_mv,gdf_lines_AC_hv, gdf_lines_AC_ehv, gdf_lines_AC_uhv, gdf_lines_AC_tf=filter_vl_and_tf(gdf_lines_AC)
 
    if grid.lines_DC != []:
        gdf_lines_HVDC = extract_line_data(grid.lines_DC, "DC")
    else:
        gdf_lines_HVDC = gpd.GeoDataFrame(columns=["geometry", "type", "name", "VL", "tf", "hover_text", "color"])
        
        
    def extract_conv_data(converters):
        line_data = []
        for conv_obj in converters:
            geometry = getattr(conv_obj, 'geometry', None)  # Ensure geometry exists
            if geometry and not geometry.is_empty:
                line_data.append({
                    "geometry": geometry,
                    "type": "conv",
                    "area":conv_obj.Node_DC.PZ,
                    "ant_viable":False,
                    "thck": getattr(conv_obj, 'np_conv', 1),
                    "name": getattr(conv_obj, 'name', 'Unknown'),
                    "hover_text": getattr(conv_obj, 'hover_text', 'No info'),
                    "color": 'purple'
                })
        return gpd.GeoDataFrame(line_data, geometry="geometry")
    
    
    if grid.Converters_ACDC != []:
        gdf_conv = extract_conv_data(grid.Converters_ACDC)
    else:
        gdf_conv = gpd.GeoDataFrame(columns=["geometry", "type", "area", "name","hover_text", "color"])
    
    # Extract node data into a GeoDataFrame
    def extract_node_data(nodes):
        
        node_data = []
        for node in nodes:
            subgraph_idx = subgraph_dict.get(node, None)
            geometry = getattr(node, 'geometry', None)
            VL = 'MV' if node.kV_base < 110 else \
                 'HV' if node.kV_base < 300 else \
                 'EHV' if node.kV_base < 500 else \
                 'UHV'
            if geometry and not geometry.is_empty:
                node_data.append({
                    "geometry": geometry,
                    "name": getattr(node, 'name', 'Unknown'),
                    "VL" :VL,
                    "area":node.PZ,
                    "hover_text": getattr(node, 'hover_text', 'No info'),
                    "load_mw": float(getattr(node, 'PLi', 0.0)) * float(grid.S_base),
                    "type": "AC" if isinstance(node, Node_AC) else "DC",
                    "color": subgraph_colors[VL].get(subgraph_idx, "black") if isinstance(node, Node_AC) else "blue"
                })
        return gpd.GeoDataFrame(node_data, geometry="geometry")

    # Create GeoDataFrame for nodes
    gdf_nodes_AC = extract_node_data(grid.nodes_AC)
    
    gdf_nodes_AC_mv,gdf_nodes_AC_hv, gdf_nodes_AC_ehv, gdf_nodes_AC_uhv, _=filter_vl_and_tf(gdf_nodes_AC)
    
    if grid.nodes_DC != []:
        gdf_nodes_DC = extract_node_data(grid.nodes_DC)
    else:
        gdf_nodes_DC = gpd.GeoDataFrame(columns=["geometry", "name", "VL", "area","hover_text","type","color"])
        
        
    def extract_gen_data(gens):
        gen_data = []
        for gen in gens:
            # Skip generators with zero (or negative) multiplicity from folium plotting.
            if gen.np_gen <= 0:
                continue
            subgraph_idx = subgraph_dict.get(gen, None)
            geometry = getattr(gen, 'geometry', None)
            VL = 'HV' if gen.kV_base < 300 else \
                 'EHV' if gen.kV_base < 500 else \
                 'UHV'
            if geometry and not geometry.is_empty:
                mw_size = gen.Max_pow_gen * grid.S_base * gen.np_gen
                gen_data.append({
                    "geometry": geometry,
                    "name": getattr(gen, 'name', 'Unknown'),
                    "VL" :VL,
                    "area":gen.PZ,
                    "hover_text": getattr(gen, 'hover_text', 'No info'),
                    "type": gen.gen_type,
                    "color": subgraph_colors[VL].get(subgraph_idx, "black"),
                    "mw_size": mw_size,
                })
        if gen_data:
            return gpd.GeoDataFrame(gen_data, geometry="geometry")
        return gpd.GeoDataFrame(
            columns=["geometry", "name", "VL", "area", "hover_text", "type", "color", "mw_size"],
            geometry="geometry",
        )
    
    
    if grid.Generators != []:
        gdf_gens = extract_gen_data(grid.Generators)
    else:
        gdf_gens = gpd.GeoDataFrame(columns=["geometry", "name", "VL", "area","hover_text","type","color"])
    
    
    def extract_renSource_data(renSources):
        gen_data = []
        for rs in renSources:
            if rs.np_rsgen <= 0:
                continue
            subgraph_idx = subgraph_dict.get(rs, None)
            geometry = getattr(rs, 'geometry', None)
            VL = 'HV' if rs.kV_base < 300 else \
                 'EHV' if rs.kV_base < 500 else \
                 'UHV'
            if geometry and not geometry.is_empty:
                mw_size = float(rs.PGi_ren_base) * float(grid.S_base) * float(rs.np_rsgen)
                gen_data.append({
                    "geometry": geometry,
                    "name": getattr(rs, 'name', 'Unknown'),
                    "VL" :VL,
                    "area":rs.PZ,
                    "hover_text": getattr(rs, 'hover_text', 'No info'),
                    "type": rs.rs_type,
                    "color": subgraph_colors[VL].get(subgraph_idx, "black"),
                    "mw_size": mw_size,
                })
        if gen_data:
            return gpd.GeoDataFrame(gen_data, geometry="geometry")
        return gpd.GeoDataFrame(
            columns=["geometry", "name", "VL", "area", "hover_text", "type", "color", "mw_size"],
            geometry="geometry",
        )
    
    
    if grid.RenSources != []:
        gdf_rsSources = extract_renSource_data(grid.RenSources)
    else:
        gdf_rsSources = gpd.GeoDataFrame(columns=["geometry", "name", "VL", "area","hover_text","type","color"])

   
    BASE_ICON_SIZE = float(base_icon_size)
    MIN_ICON_SIZE = BASE_ICON_SIZE * 0.5
    MAX_ICON_SIZE = BASE_ICON_SIZE * 2

    mw_values = [
        float(v)
        for source_gdf in (gdf_gens, gdf_rsSources)
        if 'mw_size' in source_gdf.columns
        for v in source_gdf['mw_size'].tolist()
        if float(v) > 0
    ]
    mw_min = min(mw_values) if mw_values else 0.0
    mw_max = max(mw_values) if mw_values else 0.0
    ref_mw_min = 0.5 * mw_min if mw_min > 0 else 0.0
    ref_mw_max = 2.0 * mw_max if mw_max > 0 else 0.0

    def _coord_key(geometry):
        return (round(geometry.y, 10), round(geometry.x, 10))

    # Count overlapping coordinates globally across all generation markers.
    coord_counts_all = {}
    for source_gdf in (gdf_gens, gdf_rsSources):
        for _, row in source_gdf.iterrows():
            geometry = row.get('geometry', None)
            if geometry and not geometry.is_empty:
                key = _coord_key(geometry)
                coord_counts_all[key] = coord_counts_all.get(key, 0) + 1
    coord_seen_all = {}

    def _marker_size_px(mw_value):
        if not scale_gen:
            return BASE_ICON_SIZE
        if ref_mw_max <= ref_mw_min:
            return BASE_ICON_SIZE
        norm = (mw_value - ref_mw_min) / (ref_mw_max - ref_mw_min)
        norm = max(0.0, min(1.0, norm))
        return int(round(MIN_ICON_SIZE + norm * (MAX_ICON_SIZE - MIN_ICON_SIZE)))

    
    # Function to add LineString geometries to the map
    line_size_factor = float(line_size_factor)
    if line_size_factor <= 0:
        raise ValueError("line_size_factor must be > 0.")

    def add_lines(gdf, tech_name,ant):
        
        for _, row in gdf.iterrows():
            
            # Support both 2D (x,y) and 3D (x,y,z) coordinates.
            coords = [(pt[1], pt[0]) for pt in row.geometry.coords if len(pt) >= 2]  # Folium needs (lat, lon) order
            
            if ant and row["ant_viable"]:
                if row["Direction"] == "to":
                    coords = coords[::-1]
                base_weight = 3 * row["thck"] if row["type"] == "HVDC" else 2 * row["thck"]
                weight = float(base_weight) / line_size_factor
                # Add animated AntPath
                AntPath(
                    locations=coords,
                    color=row["color"],
                    weight=weight,  # HVDC lines slightly thicker
                    opacity=0.8,
                    delay=400,  # Adjust animation speed
                    popup=folium.Popup(row["hover_text"], max_width=360, min_width=220)
                ).add_to(tech_name)
    
            else:
                base_weight = 3 * row["thck"] if row["type"] == "HVDC" else 2 * row["thck"]
                weight = float(base_weight) / line_size_factor
        
                folium.PolyLine(
                    coords,
                    color=row["color"],
                    weight=weight,  # HVDC lines slightly thicker
                    opacity=0.8,
                    popup=folium.Popup(row["hover_text"], max_width=360, min_width=220)
                ).add_to(tech_name)
        s=1
    # Calculate map center from node coordinates
    if not gdf_nodes_AC.empty:
        # Get bounds of all nodes
        bounds = gdf_nodes_AC.total_bounds
        # Calculate center point
        center_lat = (bounds[1] + bounds[3]) / 2  # (min_y + max_y) / 2
        center_lon = (bounds[0] + bounds[2]) / 2  # (min_x + max_x) / 2
        map_center = [center_lat, center_lon]
    else:
        # Fallback to North Sea if no nodes
        map_center = [56, 10]
    
    # Initialize the map, centred around the nodes
    if planar:
        # In planar coordinates, marker clustering can hide markers/layers unexpectedly.
        clustering = False
        # Planar x/y mode: do not interpret coordinates as geographic lon/lat.
        m = folium.Map(location=map_center, tiles=None, zoom_start=5, crs='Simple')
    elif tiles is not None and tiles.startswith('http'):
        # Custom tile layer with attribution
        m = folium.Map(location=map_center, zoom_start=5)
        folium.TileLayer(
            tiles=tiles,
            attr='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            name='Esri World Imagery'
        ).add_to(m)
    else:
        # Standard tile layer
        m = folium.Map(location=map_center, tiles=tiles, zoom_start=5)

    if add_marine_regions_wms:
        folium.raster_layers.WmsTileLayer(
            url="https://geo.vliz.be/geoserver/MarineRegions/wms",
            layers="MarineRegions:eez_boundaries",
            fmt="image/png",
            transparent=True,
            attr="Marine Regions",
            name="Marine Regions EEZ",
            overlay=True,
            control=True,
        ).add_to(m)
    
    # Function to add nodes with filtering by type and zone
    def add_nodes(gdf, tech_name):
        for _, row in gdf.iterrows():
            # Check if the node matches the filter criteria (both type and zone)
            folium.CircleMarker(
                location=(row.geometry.y, row.geometry.x),  # (lat, lon)
                radius=2 if row["type"] == "AC" else 3,  # DC nodes slightly larger
                color=row["color"],
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(row["hover_text"], max_width=360, min_width=220)
            ).add_to(tech_name)

    def add_load_markers(gdf, tech_name):
        try:
            load_icon_path = str(resources.files('pyflow_acdc').joinpath('folium_images').joinpath('load.png'))
        except Exception:
            load_icon_path = os.path.join(os.path.dirname(__file__), 'folium_images', 'load.png')
        load_icon_px = int(round(BASE_ICON_SIZE))
        for _, row in gdf.iterrows():
            if float(row.get("load_mw", 0.0)) <= 0:
                continue
            folium.Marker(
                location=(row.geometry.y, row.geometry.x),
                popup=folium.Popup(row["hover_text"], max_width=360, min_width=220),
                icon=folium.CustomIcon(
                    icon_image=load_icon_path,
                    icon_size=(load_icon_px, load_icon_px),
                    icon_anchor=(0, 0),
                ),
            ).add_to(tech_name)
    
    default_type_keys = _default_type_keys()

    try:
        base_icon_dir = resources.files('pyflow_acdc').joinpath('folium_images')
        use_importlib_resources = True
    except Exception:
        base_icon_dir = os.path.join(os.path.dirname(__file__), 'folium_images')
        use_importlib_resources = False

    def add_markers(gdf, tech_name):  
        
        if clustering == True:
            cluster = MarkerCluster().add_to(tech_name)  # Add clustering per type
        else:
            cluster = tech_name
        for _, row in gdf.iterrows():
            if row['geometry'] and not row['geometry'].is_empty:
                lat, lon = row['geometry'].y, row['geometry'].x
                key = (round(lat, 10), round(lon, 10))
                typ = str(row['type']).lower()
                typ_icon = typ.replace(" ", "_") if typ in default_type_keys else "other"

                total_at_coord = coord_counts_all.get(key, 1)
                used_at_coord = coord_seen_all.get(key, 0)
                coord_seen_all[key] = used_at_coord + 1

                marker_size_px = _marker_size_px(float(row.get('mw_size', 0.0)))
                icon_size = (marker_size_px, marker_size_px)
                center = marker_size_px // 2
                if total_at_coord > 1:
                    ring_size = 8
                    ring = used_at_coord // ring_size
                    pos_in_ring = used_at_coord % ring_size
                    points_this_ring = min(total_at_coord - ring * ring_size, ring_size)
                    angle = (2 * np.pi * pos_in_ring) / max(points_this_ring, 1)
                    radius_px = 14 + 8 * ring
                    dx = int(round(radius_px * np.cos(angle)))
                    dy = int(round(radius_px * np.sin(angle)))
                    icon_anchor = (center + dx, center + dy)
                else:
                    # Match the previous visual behavior for single markers.
                    icon_anchor = (marker_size_px, marker_size_px)

                if use_importlib_resources:
                    icon_path = str(base_icon_dir.joinpath(f'{typ_icon}.png'))
                else:
                    icon_path = os.path.join(base_icon_dir, f'{typ_icon}.png')

                folium.Marker(
                    location=(lat, lon),  # Keep marker on exact coordinate
                    popup=folium.Popup(row["hover_text"], max_width=360, min_width=220),  # Display name on click
                    icon=folium.CustomIcon(
                        icon_image=icon_path,
                        icon_size=icon_size,
                        icon_anchor=icon_anchor,
                    )
                ).add_to(cluster)
                
    
    
    mv_AC  = folium.FeatureGroup(name="MVAC Lines <110kV")
    hv_AC  = folium.FeatureGroup(name="HVAC Lines <300kV")
    ehv_AC = folium.FeatureGroup(name="HVAC Lines <500kV")
    uhv_AC = folium.FeatureGroup(name="HVAC Lines")
    hvdc   = folium.FeatureGroup(name="HVDC Lines")
    convs  = folium.FeatureGroup(name="Converters")
    transformers = folium.FeatureGroup(name="Transformers")
    ct_AC = folium.FeatureGroup(name="Conductor Size Selection")
    exp_lines = folium.FeatureGroup(name="Exp Lines")
    rec_lines = folium.FeatureGroup(name="Rec Lines")
    loads_fg = folium.FeatureGroup(name="Loads", show=bool(show_all))
    
    if ant_path == 'All' or ant_path == 'Reduced':
        ant = True
    else:
        ant = False
        
    add_lines(gdf_lines_AC_mv, mv_AC,ant)    
    add_lines(gdf_lines_AC_hv, hv_AC,ant)
    add_lines(gdf_lines_AC_ehv, ehv_AC,ant)
    add_lines(gdf_lines_AC_uhv, uhv_AC,ant)
    add_lines(gdf_lines_AC_ct, ct_AC,ant)
    add_lines(gdf_lines_AC_exp, exp_lines,ant)
    add_lines(gdf_lines_AC_rec, rec_lines,ant)
    add_lines(gdf_lines_AC_tf, transformers,ant)
    add_lines(gdf_lines_HVDC, hvdc,ant)
    add_lines(gdf_conv, convs, ant)
    
    add_nodes(gdf_nodes_AC_mv, mv_AC)
    add_nodes(gdf_nodes_AC_hv, hv_AC)
    add_nodes(gdf_nodes_AC_ehv, ehv_AC)
    add_nodes(gdf_nodes_AC_uhv, uhv_AC)
    add_nodes(gdf_nodes_DC, hvdc)
    if plot_load:
        add_load_markers(gdf_nodes_AC, loads_fg)
        add_load_markers(gdf_nodes_DC, loads_fg)

    
    layer_names = grid.generation_types
    # Dictionary to store FeatureGroups for each generation type (lowercase key for robust matching)
    layers = {name.lower(): folium.FeatureGroup(name=name, show=bool(show_all)) for name in layer_names}
    
    
    # Add filtered layers to map
    mv_AC.add_to(m)  if len(mv_AC._children) > 0 else None
    hv_AC.add_to(m)  if len(hv_AC._children) > 0 else None
    ehv_AC.add_to(m) if len(ehv_AC._children) > 0 else None
    uhv_AC.add_to(m) if len(uhv_AC._children) > 0 else None
    hvdc.add_to(m)   if len(hvdc._children) > 0 else None
    convs.add_to(m)  if len(convs._children) > 0 else None
    transformers.add_to(m) if len(transformers._children) > 0 else None
    ct_AC.add_to(m) if len(ct_AC._children) > 0 else None
    exp_lines.add_to(m)    if len(exp_lines._children) > 0 else None
    rec_lines.add_to(m) if len(rec_lines._children) > 0 else None
    loads_fg.add_to(m) if plot_load and len(loads_fg._children) > 0 else None
        
    # Split gdf_gens by type and add markers for each type
    for gen_type, subset in gdf_gens.groupby('type'):  # Split by 'type'
        key = str(gen_type).lower()
        if key not in layers:
            layers[key] = folium.FeatureGroup(name=str(gen_type), show=bool(show_all))
        add_markers(subset, layers[key])
    
    for gen_type, subset in gdf_rsSources.groupby('type'):  # Split by 'type'
        key = str(gen_type).lower()
        if key not in layers:
            layers[key] = folium.FeatureGroup(name=str(gen_type), show=bool(show_all))
        add_markers(subset, layers[key])
    for layer in layers.values():
        if len(layer._children) > 0:  # Check if the layer has children
            layer.add_to(m)

    # Fit to data bounds for better initial framing (especially in planar mode).
    if not gdf_nodes_AC.empty:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    if polygon is not None:
        folium.GeoJson(
            polygon,
            name="Area to Study",
            style_function=lambda x: {"color": "blue", "weight": 2, "opacity": 0.6, "fill": False},
            show=False
        ).add_to(m)

    if linestrings is not None:
        # Handle both single linestring and list of linestrings
        if not isinstance(linestrings, list):
            linestrings = [linestrings]
        
        for linestring in linestrings:
            
            coords = [(y, x) for x, y in linestring.coords]  # convert (lon, lat) → (lat, lon)

            folium.PolyLine(
                coords,
                color="black",
                weight=2,
                opacity=1
            ).add_to(m)
            

    Draw(   export=True,  # Allows downloading edited layers
            edit_options={'poly': {'allowIntersection': False}},  # Prevents self-intersecting edits
            draw_options={'polygon': True, 'polyline': True, 'rectangle': True, 'circle': False},
        ).add_to(m)


    # Draw().add_to(m)
    if coloring == 'Efficiency':
        colormap = branca.colormap.LinearColormap(
            colors=["red","yellow", "green"],
            vmin=70, 
            vmax=100
            )
        colormap.caption = "Efficiency Scale"  # Optional: Set a caption for clarity
        m.add_child(colormap)
        
    # Add layer control
    folium.LayerControl().add_to(m)
    # Save and display the map
    map_filename = f"{name}.html"
    # Save and display the map
    m.save(map_filename)  # Open this file in a browser to viewm
    abs_map_filename = os.path.abspath(map_filename)
    
    # Automatically open the map in the default web browser
    if show:
        webbrowser.open(f"file://{abs_map_filename}")
    return m

def _ts_index_to_iso_strings(index):
    iso_times = []
    base_time = datetime(2000, 1, 1, 0, 0, 0)
    for i, val in enumerate(index):
        if hasattr(val, "isoformat"):
            iso_times.append(val.isoformat())
            continue
        try:
            offset = int(float(val))
            ts = base_time + timedelta(hours=offset)
        except Exception:
            ts = base_time + timedelta(hours=i)
        iso_times.append(ts.isoformat())
    return iso_times

def _leaflet_color(color_value):
    """Return a Leaflet-safe color string (prefer #RRGGBB)."""
    if isinstance(color_value, str):
        c = color_value.strip()
        if c.startswith("#") and len(c) == 9:
            return c[:7]
        return c
    return "black"

def plot_folium_ts_results(
    grid,
    name=None,
    tiles="CartoDB Positron",
    start=None,
    end=None,
    show=True,
    min_weight=1.5,
    max_weight=8.0,
    add_legend=True,
    legend_position="topright",
    line_size_factor=1.0,
):
    line_size_factor = float(line_size_factor)
    if line_size_factor <= 0:
        raise ValueError("line_size_factor must be > 0.")

    if name is None:
        name = f"{grid.name}_ts_results"

    create_geometries_from_coords(grid)
    ac_loading = grid.time_series_results.get("ac_loading", None)
    dc_loading = grid.time_series_results.get("dc_loading", None)
    ac_pref = ac_loading.add_prefix("AC_Load_") if ac_loading is not None else pd.DataFrame()
    dc_pref = dc_loading.add_prefix("DC_Load_") if dc_loading is not None else pd.DataFrame()
    line_loading_df = pd.concat([ac_pref, dc_pref], axis=1)
    if line_loading_df.empty:
        raise ValueError("grid.time_series_results['ac_loading'/'dc_loading'] are required and cannot be empty.")

    if start is not None or end is not None:
        try:
            if start is not None and end is not None:
                line_loading_df = line_loading_df.loc[start:end]
            elif start is not None:
                line_loading_df = line_loading_df.loc[start:]
            else:
                line_loading_df = line_loading_df.loc[:end]
        except Exception:
            start_i = 0 if start is None else int(start)
            end_i = len(line_loading_df) if end is None else int(end) + 1
            line_loading_df = line_loading_df.iloc[start_i:end_i]

    if line_loading_df.empty:
        raise ValueError("No time steps available after applying start/end selection.")

    colormap = branca.colormap.LinearColormap(colors=["green", "yellow", "red"], vmin=0, vmax=100)
    lines_ac = list(getattr(grid, "lines_AC", []) or [])
    lines_ac_tf = list(getattr(grid, "lines_AC_tf", []) or [])
    lines_ac_rec = list(getattr(grid, "lines_AC_rec", []) or [])
    lines_ac_exp = list(getattr(grid, "lines_AC_exp", []) or [])
    lines_ac_ct = list(getattr(grid, "lines_AC_ct", []) or [])
    lines_dc = list(getattr(grid, "lines_DC", []) or [])
    all_lines = lines_ac + lines_ac_tf + lines_ac_rec + lines_ac_exp + lines_ac_ct + lines_dc
    dc_names = {line.name for line in lines_dc}

    iso_times = _ts_index_to_iso_strings(line_loading_df.index)

    features = []
    for row_idx, (_, row) in enumerate(line_loading_df.iterrows()):
        t_iso = iso_times[row_idx]
        for line in all_lines:
            geometry = getattr(line, "geometry", None)
            if geometry is None or geometry.is_empty:
                continue

            if line.name in dc_names:
                load_col = f"DC_Load_{line.name}"
            else:
                load_col = f"AC_Load_{line.name}"

            if load_col not in row:
                continue

            load_frac = float(row[load_col]) if np.isfinite(row[load_col]) else 0.0
            load_pct = max(0.0, load_frac * 100.0)
            n_parallel = float(getattr(line, "np_line", 1.0))
            if not np.isfinite(n_parallel) or n_parallel <= 0:
                n_parallel = 1.0
            n_cap = max(1.0, min(6.0, n_parallel))
            width_scale = (n_cap - 1.0) / 5.0
            weight = float(min_weight + (max_weight - min_weight) * width_scale) / line_size_factor
            color = _leaflet_color(colormap(min(load_pct, 100.0)))

            coords_lonlat = [[pt[0], pt[1]] for pt in geometry.coords if len(pt) >= 2]
            if len(coords_lonlat) < 2:
                continue

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords_lonlat,
                },
                "properties": {
                    "time": t_iso,
                    "times": [t_iso],
                    "style": {
                        "color": color,
                        "weight": weight,
                        "opacity": 0.9,
                    },
                },
            })

    if not features:
        raise ValueError(
            "No line TS features were built. Ensure time_series_results['ac_loading'/'dc_loading'] "
            "have columns matching line names."
        )

    node_geometries = []
    for node in list(grid.nodes_AC) + list(grid.nodes_DC):
        geom = getattr(node, "geometry", None)
        if geom is not None and not geom.is_empty:
            node_geometries.append(geom)

    if node_geometries:
        minx = min(g.x for g in node_geometries)
        miny = min(g.y for g in node_geometries)
        maxx = max(g.x for g in node_geometries)
        maxy = max(g.y for g in node_geometries)
        map_center = [(miny + maxy) / 2.0, (minx + maxx) / 2.0]
    else:
        map_center = [56, 10]

    m = folium.Map(location=map_center, tiles=tiles, zoom_start=5)

    for node in grid.nodes_AC:
        geom = getattr(node, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        folium.CircleMarker(
            location=(geom.y, geom.x),
            radius=2,
            color="black",
            fill=True,
            fill_opacity=0.8,
            weight=1,
        ).add_to(m)
    for node in grid.nodes_DC:
        geom = getattr(node, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        folium.CircleMarker(
            location=(geom.y, geom.x),
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.8,
            weight=1,
        ).add_to(m)

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1H",
        duration="PT1H",
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=8,
        loop_button=True,
        date_options="YYYY-MM-DD HH:mm",
        time_slider_drag_update=True,
    ).add_to(m)

    if add_legend:
        pos_map = {
            "topright": ("16px", "16px", "", ""),
            "topleft": ("16px", "", "16px", ""),
            "bottomright": ("", "16px", "", "80px"),
            "bottomleft": ("", "", "16px", "80px"),
        }
        top, right, left, bottom = pos_map.get(str(legend_position).lower(), pos_map["topright"])
        top_css = f"top: {top};" if top else ""
        right_css = f"right: {right};" if right else ""
        left_css = f"left: {left};" if left else ""
        bottom_css = f"bottom: {bottom};" if bottom else ""
        legend_html = """
        <div style="
            position: fixed;
            __TOP__
            __RIGHT__
            __LEFT__
            __BOTTOM__
            z-index: 9999;
            background: white;
            border: 1px solid #777;
            border-radius: 6px;
            padding: 10px 12px;
            font-size: 12px;
            line-height: 1.25;
            box-shadow: 0 1px 4px rgba(0,0,0,0.25);
        ">
          <div style="font-weight: 600; margin-bottom: 6px;">TS Flow Legend</div>
          <div style="margin-bottom: 4px;">Color = loading</div>
          <div style="display:flex; align-items:center; gap:8px; margin-bottom: 8px;">
            <div style="width:120px; height:10px; background: linear-gradient(to right, green, yellow, red); border:1px solid #aaa;"></div>
            <div style="font-size:11px;">0% → 100%</div>
          </div>
          <div style="margin-bottom: 2px;">Thickness = number of circuits (`n`/`np_line`)</div>
          <div style="font-size:11px; color:#444;">Thin: n=1, Thick: n≥6</div>
        </div>
        """
        legend_html = (
            legend_html
            .replace("__TOP__", top_css)
            .replace("__RIGHT__", right_css)
            .replace("__LEFT__", left_css)
            .replace("__BOTTOM__", bottom_css)
        )
        m.get_root().html.add_child(folium.Element(legend_html))

    if node_geometries:
        m.fit_bounds([[miny, minx], [maxy, maxx]])

    map_filename = f"{name}.html"
    m.save(map_filename)
    abs_map_filename = os.path.abspath(map_filename)
    if show:
        webbrowser.open(f"file://{abs_map_filename}")
    return m

def plot_folium_inv_results(
    grid,
    name=None,
    source="auto",
    tiles="CartoDB Positron",
    planar=False,
    show=True,
    min_weight=1.5,
    max_weight=8.0,
    show_installed=True,
    show_decommissioned=True,
    inv_dropdown_period=False,
    line_size_factor=1.0,
):
    line_size_factor = float(line_size_factor)
    if line_size_factor <= 0:
        raise ValueError("line_size_factor must be > 0.")

    if name is None:
        name = f"{grid.name}_inv_results"

    create_geometries_from_coords(grid)

    def _pick_results_df():
        if source == "auto":
            candidates = [
                getattr(grid, "MP_TEP_results", None),
                getattr(grid, "Seq_MS_STEP_results", None),
                getattr(grid, "Seq_STEP_results", None),
            ]
            for cand in candidates:
                if isinstance(cand, pd.DataFrame) and not cand.empty:
                    return cand
            return None
        if source == "mp":
            return getattr(grid, "MP_TEP_results", None)
        if source == "seq_ms":
            return getattr(grid, "Seq_MS_STEP_results", None)
        if source == "seq":
            return getattr(grid, "Seq_STEP_results", None)
        raise ValueError("source must be one of: auto, mp, seq, seq_ms")

    inv_df = _pick_results_df()
    if inv_df is None or inv_df.empty:
        raise ValueError("No investment results DataFrame found for selected source.")

    period_ids = []
    for col in inv_df.columns:
        if col.startswith("Active_") and col[len("Active_"):].isdigit():
            period_ids.append(int(col[len("Active_"):]))
    period_ids = sorted(set(period_ids))
    if not period_ids:
        raise ValueError("Investment results require Active_<period> columns.")

    years_per_period = int(getattr(grid, "TEP_n_years", 1) or 1)
    base_time = datetime(2000, 1, 1, 0, 0, 0)
    iso_times = [
        (base_time + timedelta(days=365 * years_per_period * (p - 1))).isoformat()
        for p in period_ids
    ]
    time_by_period = {p: iso_times[i] for i, p in enumerate(period_ids)}

    lines_ac = list(getattr(grid, "lines_AC", []) or [])
    lines_ac_tf = list(getattr(grid, "lines_AC_tf", []) or [])
    lines_ac_rec = list(getattr(grid, "lines_AC_rec", []) or [])
    lines_ac_exp = list(getattr(grid, "lines_AC_exp", []) or [])
    lines_ac_ct = list(getattr(grid, "lines_AC_ct", []) or [])
    lines_dc = list(getattr(grid, "lines_DC", []) or [])
    all_lines = lines_ac + lines_ac_tf + lines_ac_rec + lines_ac_exp + lines_ac_ct + lines_dc

    lines_by_name = {str(line.name): line for line in all_lines}
    lower_lines_by_name = {str(line.name).lower(): line for line in all_lines}

    def _line_color(line_obj):
        if line_obj in lines_dc:
            return "royalblue"
        if line_obj in lines_ac_exp:
            return "darkorange"
        if line_obj in lines_ac_rec:
            return "seagreen"
        if line_obj in lines_ac_ct:
            return "teal"
        if getattr(line_obj, "isTf", False):
            return "firebrick"
        return "black"

    def _weight_from_active(active_value, max_active):
        if max_active <= 0:
            return float(min_weight) / line_size_factor
        scale = max(0.0, min(1.0, float(active_value) / float(max_active)))
        return float(min_weight + (max_weight - min_weight) * scale) / line_size_factor

    max_active = 0.0
    active_map = {}
    installed_map = {}
    decomm_map = {}

    for _, row in inv_df.iterrows():
        element_name = str(row.get("Element", "")).strip()
        if not element_name:
            continue
        line_obj = lines_by_name.get(element_name) or lower_lines_by_name.get(element_name.lower())
        if line_obj is None:
            continue

        active_map[line_obj] = {}
        installed_map[line_obj] = {}
        decomm_map[line_obj] = {}
        for p in period_ids:
            a_col = f"Active_{p}"
            i_col = f"Installed_{p}"
            d_col = f"Decommissioned_{p}"
            a_val = float(row[a_col]) if a_col in row and np.isfinite(row[a_col]) else 0.0
            i_val = float(row[i_col]) if i_col in row and np.isfinite(row[i_col]) else 0.0
            d_val = float(row[d_col]) if d_col in row and np.isfinite(row[d_col]) else 0.0
            active_map[line_obj][p] = a_val
            installed_map[line_obj][p] = i_val
            decomm_map[line_obj][p] = d_val
            max_active = max(max_active, a_val)

    # Keep non-investment lines visible as static references through all periods.
    for line_obj in all_lines:
        if line_obj in active_map:
            continue
        base_count = float(getattr(line_obj, "np_line", 1.0))
        if base_count <= 0:
            base_count = 1.0
        active_map[line_obj] = {p: base_count for p in period_ids}
        installed_map[line_obj] = {p: 0.0 for p in period_ids}
        decomm_map[line_obj] = {p: 0.0 for p in period_ids}
        max_active = max(max_active, base_count)

    use_dropdown = bool(inv_dropdown_period)
    features = [] if not use_dropdown else None
    features_by_period = {p: [] for p in period_ids} if use_dropdown else None

    for line_obj in all_lines:
        geometry = getattr(line_obj, "geometry", None)
        if geometry is None or geometry.is_empty:
            continue
        coords_lonlat = [[pt[0], pt[1]] for pt in geometry.coords if len(pt) >= 2]
        if len(coords_lonlat) < 2:
            continue

        for p in period_ids:
            active_val = float(active_map[line_obj].get(p, 0.0))
            if active_val <= 1e-9:
                continue

            style = {
                "color": _line_color(line_obj),
                "weight": _weight_from_active(active_val, max_active),
                "opacity": 0.9,
            }

            if use_dropdown:
                features_by_period[p].append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                    "properties": {"style": style},
                })
            else:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                    "properties": {"times": [time_by_period[p]], "style": style},
                })

            if (not use_dropdown) and show_installed and installed_map[line_obj].get(p, 0.0) > 1e-9:
                installed_style = {
                    "color": "limegreen",
                    "weight": max(style["weight"] * 0.55, 1.5),
                    "opacity": 0.95,
                    "dashArray": "2, 6",
                }
                if use_dropdown:
                    features_by_period[p].append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                        "properties": {"style": installed_style},
                    })
                else:
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                        "properties": {
                            "times": [time_by_period[p]],
                            "style": installed_style,
                        },
                    })

            if (not use_dropdown) and show_decommissioned and decomm_map[line_obj].get(p, 0.0) > 1e-9:
                decomm_style = {
                    "color": "crimson",
                    "weight": max(style["weight"] * 0.45, 1.2),
                    "opacity": 0.95,
                    "dashArray": "8, 8",
                }
                if use_dropdown:
                    features_by_period[p].append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                        "properties": {"style": decomm_style},
                    })
                else:
                    features.append({
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                        "properties": {
                            "times": [time_by_period[p]],
                            "style": decomm_style,
                        },
                    })

    if (not use_dropdown) and not features:
        raise ValueError("No investment features were built from the selected results source.")

    node_geometries = []
    for node in list(getattr(grid, "nodes_AC", []) or []) + list(getattr(grid, "nodes_DC", []) or []):
        geom = getattr(node, "geometry", None)
        if geom is not None and not geom.is_empty:
            node_geometries.append(geom)

    if node_geometries:
        minx = min(g.x for g in node_geometries)
        miny = min(g.y for g in node_geometries)
        maxx = max(g.x for g in node_geometries)
        maxy = max(g.y for g in node_geometries)
        map_center = [(miny + maxy) / 2.0, (minx + maxx) / 2.0]
    else:
        map_center = [56, 10]

    if planar:
        # Planar x/y mode: do not interpret coordinates as geographic lon/lat.
        m = folium.Map(location=map_center, tiles=None, zoom_start=5, crs="Simple")
    else:
        m = folium.Map(location=map_center, tiles=tiles, zoom_start=5)

    for node in getattr(grid, "nodes_AC", []) or []:
        geom = getattr(node, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        folium.CircleMarker(
            location=(geom.y, geom.x),
            radius=2,
            color="black",
            fill=True,
            fill_opacity=0.8,
            weight=1,
        ).add_to(m)
    for node in getattr(grid, "nodes_DC", []) or []:
        geom = getattr(node, "geometry", None)
        if geom is None or geom.is_empty:
            continue
        folium.CircleMarker(
            location=(geom.y, geom.x),
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.8,
            weight=1,
        ).add_to(m)

    if use_dropdown:
        # One Leaflet layer per investment "mode" (base + each investment period).
        # We toggle by setting per-line styles (opacity/weight), which is more robust than add/remove.
        def _style_fn(feature):
            props = feature.get("properties", {}) or {}
            return props.get("style", {}) or {}

        period_select_id = f"inv_period_select_{abs(hash(name))}"

        # Build base features from nominal np_line (no direction coloring in dropdown mode).
        base_features = []
        max_base_active = 0.0
        for line_obj in all_lines:
            geometry = getattr(line_obj, "geometry", None)
            if geometry is None or geometry.is_empty:
                continue
            base_count = float(getattr(line_obj, "np_line", 1.0) or 1.0)
            max_base_active = max(max_base_active, base_count)

        max_active_all = max(max_active, max_base_active) if max_active is not None else max_base_active
        if max_active_all <= 0:
            max_active_all = 1.0

        for line_obj in all_lines:
            geometry = getattr(line_obj, "geometry", None)
            if geometry is None or geometry.is_empty:
                continue
            coords_lonlat = [[pt[0], pt[1]] for pt in geometry.coords if len(pt) >= 2]
            if len(coords_lonlat) < 2:
                continue
            base_count = float(getattr(line_obj, "np_line", 1.0) or 1.0)
            if base_count <= 1e-9:
                continue
            style = {
                "color": _line_color(line_obj),
                "weight": _weight_from_active(base_count, max_active_all),
                "opacity": 0.9,
            }
            base_features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords_lonlat},
                "properties": {"style": style},
            })

        all_keys = ["base"] + [str(p) for p in period_ids]
        default_key = "base"

        fg_by_key_var = {}
        dropdown_options_html = []

        # Base FG
        fg_base = folium.FeatureGroup(name="Base (nominal np)", show=True)
        fg_by_key_var["base"] = fg_base.get_name()
        if base_features:
            folium.GeoJson({"type": "FeatureCollection", "features": base_features}, style_function=_style_fn).add_to(fg_base)
        fg_base.add_to(m)
        dropdown_options_html.append(f'<option value="base" {"selected" if default_key=="base" else ""}>Base</option>')

        # Period FGs
        for p in period_ids:
            key = str(p)
            fg = folium.FeatureGroup(name=f"Inv period {p}", show=False)
            fg_by_key_var[key] = fg.get_name()
            fc = {"type": "FeatureCollection", "features": features_by_period.get(p, [])}
            if fc["features"]:
                folium.GeoJson(fc, style_function=_style_fn).add_to(fg)
            fg.add_to(m)
            dropdown_options_html.append(f'<option value="{key}" {"selected" if default_key==key else ""}>Period {p}</option>')

        dropdown_html = f"""
        <div style="
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 9999;
            background: white;
            border: 1px solid #777;
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.25);
        ">
          <div style="font-weight: 600; margin-bottom: 6px;">Investment selection</div>
          <select id="{period_select_id}" style="padding: 3px; font-size: 12px;">
            {''.join(dropdown_options_html)}
          </select>
        </div>
        """
        m.get_root().html.add_child(folium.Element(dropdown_html))

        fg_map_js = ", ".join([f"'{k}': {fg_by_key_var[k]}" for k in all_keys if k in fg_by_key_var])
        map_var = m.get_name()
        js = f"""
        <script>
        (function() {{
          var selectEl = document.getElementById("{period_select_id}");
          var mapObj = {map_var};
          var fgByKey = {{{fg_map_js}}};
          // Toggle visibility by adding/removing the FeatureGroup layer itself.
          // This is robust for GeoJson-in-FeatureGroup (where eachLayer() hits the GeoJson container, not its features).
          function setKey(selKey) {{
            Object.keys(fgByKey).forEach(function(key) {{
              var fg = fgByKey[key];
              if (!fg) return;
              if (key === selKey) {{
                if (!mapObj.hasLayer(fg)) mapObj.addLayer(fg);
              }} else {{
                if (mapObj.hasLayer(fg)) mapObj.removeLayer(fg);
              }}
            }});
          }}

          if (selectEl) {{
            selectEl.addEventListener("change", function() {{
              setKey(selectEl.value);
            }});
            setKey(selectEl.value);
          }}
        }})();
        </script>
        """
        m.get_root().html.add_child(folium.Element(js))
    else:
        TimestampedGeoJson(
            {"type": "FeatureCollection", "features": features},
            period=f"P{max(years_per_period, 1)}Y",
            duration=f"P{max(years_per_period, 1)}Y",
            add_last_point=False,
            auto_play=False,
            loop=False,
            max_speed=8,
            loop_button=True,
            date_options="YYYY",
            time_slider_drag_update=True,
        ).add_to(m)

    if node_geometries:
        m.fit_bounds([[miny, minx], [maxy, maxx]])

    map_filename = f"{name}.html"
    m.save(map_filename)
    abs_map_filename = os.path.abspath(map_filename)
    if show:
        webbrowser.open(f"file://{abs_map_filename}")
    return m


def _folium_has_inv_results(grid):
    candidates = [
        getattr(grid, 'MP_TEP_results', None),
        getattr(grid, 'Seq_MS_STEP_results', None),
        getattr(grid, 'Seq_STEP_results', None),
    ]
    for cand in candidates:
        if isinstance(cand, pd.DataFrame) and not cand.empty:
            return True
    return False


def _folium_has_ts_line_loading(grid):
    if not getattr(grid, 'Time_series_ran', False):
        return False
    tsr = getattr(grid, 'time_series_results', None) or {}
    ll = tsr.get('line_loading')
    return ll is not None and not getattr(ll, 'empty', True)


def _resolve_folium_mode(grid, mode):
    """mode: 'auto' | 'network' | 'ts' | 'inv'."""
    gm = getattr(grid, 'folium_mode', 'auto')
    if mode == 'auto' and gm in ('network', 'ts', 'inv'):
        return gm
    if mode != 'auto':
        return mode
    if gm in ('network', 'ts', 'inv'):
        return gm
    if _folium_has_ts_line_loading(grid):
        return 'ts'
    if _folium_has_inv_results(grid) and (
        getattr(grid, 'TEP_run', False)
        or getattr(grid, 'MP_TEP_run', False)
        or getattr(grid, 'MP_MS_TEP_run', False)
        or getattr(grid, 'Seq_STEP_run', False)
        or getattr(grid, 'Seq_MS_STEP_run', False)
    ):
        return 'inv'
    return 'network'


def plot_folium(grid, mode='auto', **kwargs):
    """
    Choose the folium helper using the same run flags as ``Grid.reset_run_flags``.

    mode: 'auto' | 'network' | 'ts' | 'inv'

    * **auto** — ``grid.folium_mode`` if set to a concrete mode; else prefer a TS
      loading animation if ``Time_series_ran`` and ``line_loading`` exist; else an
      investment timeline map if a MP/Seq results table exists and any of
      ``TEP_run``, ``MP_TEP_run``, ``MP_MS_TEP_run``, ``Seq_STEP_run``,
      ``Seq_MS_STEP_run`` is true; else static ``plot_folium_network``.

    Extra keyword arguments are forwarded to the selected function.
    """
    resolved = _resolve_folium_mode(grid, mode)
    if resolved == 'ts':
        return plot_folium_ts_results(grid, **kwargs)
    if resolved == 'inv':
        return plot_folium_inv_results(grid, **kwargs)
    return plot_folium_network(grid, **kwargs)





def _default_type_keys():
    from .Classes import Grid
    return set(
        [t.lower() for t in Grid.DEFAULT_GENERATION_TYPES] +
        [t.lower() for t in Grid.DEFAULT_RENEWABLE_TYPES]
    )