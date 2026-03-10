# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 09:06:32 2024

@author: BernardoCastro
"""

import sys
import networkx as nx
import pandas as pd
import numpy as np

import yaml
from pathlib import Path


def pol2cart(r, theta):
    x = r*np.cos(theta)
    y = r*np.sin(theta)
    return x, y


def pol2cartz(r, theta):
    x = r*np.cos(theta)
    y = r*np.sin(theta)
    z = x+1j*y
    return z


def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    return rho, theta


def cartz2pol(z):
    r = np.abs(z)
    theta = np.angle(z)
    return r, theta

class Grid:
    DEFAULT_GENERATION_TYPES = [
        "nuclear",
        "hard coal",
        "hydro",
        "oil",
        "lignite",
        "natural gas",
        "solid biomass",
        "other",
        "waste",
        "biogas",
        "geothermal",
        "ccgt",
        "diesel",
        "shunt reactor",
        ]

    DEFAULT_RENEWABLE_TYPES = [
        "wind",
        "solar",
        "offshore wind",
        "onshore wind",
    ]

    def __init__(self, S_base: float, nodes_AC: list = None, lines_AC: list = None, Converters: list = None, nodes_DC: list = None, lines_DC: list = None):
        
        self.Graph_toPlot= nx.MultiGraph()
        self.node_positions={}
        self.S_base = S_base

        self._nodes_AC = nodes_AC if nodes_AC else []
        self._nodes_DC = nodes_DC if nodes_DC else []
        
        self._nodes_dict_AC = None  # Cache for AC nodes dictionary
        self._pq_nodes = None  # Cache for PQ nodes
        self._pv_nodes = None  # Cache for PV nodes
        self._slack_nodes = None  # Cache for Slack nodes
        
        self._nodes_dict_DC = None  # Cache for DC nodes dictionary
        self._PAC_nodes = None  
        self._P_nodes = None  
        self._droop_nodes = None  
        self._slackDC_nodes = None  
        
        
        self.lines_AC = []
        if lines_AC:
            for line in lines_AC:
                # Set grid's S_base for each line
                line.S_base = self.S_base
                self.lines_AC.append(line)
        self.lines_AC_exp = []
        self.lines_AC_rec = []
        self.lines_AC_tf  = []

        self.Cable_options=[]
        self.lines_AC_ct=[]
        self.cab_types_allowed=3
        self.crossing_groups = []
        self.MIP_time = None
        self.MIP_check = False
        self.act_gen = False


        self.Converters_ACDC = Converters if Converters else []
        for conv in self.Converters_ACDC:
            if not hasattr(conv, 'basekA'):
                conv.basekA    = self.S_base/(np.sqrt(3)*conv.AC_kV_base)
                
                conv.a_conv = conv.a_conv_og/self.S_base
                conv.b_conv = conv.b_conv_og*conv.basekA/self.S_base
                conv.c_inver = conv.c_inver_og*conv.basekA**2/self.S_base
                conv.c_inver = conv.c_inver_og*conv.basekA**2/self.S_base
                conv.c_rect = conv.c_rect_og*conv.basekA**2/self.S_base
                
            # if not hasattr(conv, 'basekA_DC'):    
            #     conv.basekA_DC = self.S_base/(conv.DC_kV_base)
            #     conv.ra_rect  = conv.c_rect_og*conv.basekA_DC**2/self.S_base
            #     conv.ra_inver = conv.c_inver_og*conv.basekA_DC**2/self.S_base
                
        self.lines_DC = []
        if lines_DC:
            for line in lines_DC:
                # Set grid's S_base for each line
                line.S_base = self.S_base
                self.lines_DC.append(line)

        self.CFC_DC = []

        self.Converters_DCDC = []

        self.slack_bus_number_AC = []
        self.slack_bus_number_DC = []
        

        self.iter_flow_AC = []
        self.iter_flow_DC = []

        self.LCoE = 1
        self.OPF_obj = {
       'Ext_Gen': {'w': 0},
       'Energy_cost': {'w': 0},
       'Curtailment_Red': {'w': 0},
       'AC_losses': {'w': 0},
       'DC_losses': {'w': 0},
       'Converter_Losses': {'w': 0},
       'General_Losses': {'w': 0},
       'PZ_cost_of_generation': {'w': 0},
       'Renewable_profit': {'w': 0},
       'Gen_set_dev': {'w': 0}
    }
        self.reset_run_flags()
    
        self.TEP_multiScenario_res=None
        self.MP_TEP_res=None
        self.time_series_results = {
            'PF_results': pd.DataFrame(),  # Time_series_res
            'line_loading': pd.DataFrame(),  # Time_series_line_res
            'ac_line_loading': pd.DataFrame(),  # TS_AC_line_res
            'dc_line_loading': pd.DataFrame(),  # TS_DC_line_res
            'grid_loading': pd.DataFrame(),  # Time_series_grid_loading
            'converter_p_dc': pd.DataFrame(),  # Time_series_Opt_res_P_conv_DC
            'converter_q_ac': pd.DataFrame(),  # Time_series_Opt_res_Q_conv_AC
            'converter_p_ac': pd.DataFrame(),  # Time_series_Opt_res_P_conv_AC
            'real_power_opf': pd.DataFrame(),  # Time_series_Opt_res_P_extGrid
            'reactive_power_opf': pd.DataFrame(),  # Time_series_Opt_res_Q_extGrid
            'curtailment': pd.DataFrame(),  # Time_series_Opt_curtailment
            'converter_loading': pd.DataFrame(),  # Time_series_conv_res
            'real_power_by_zone': pd.DataFrame(),  # Time_series_Opt_Gen_perPriceZone
            'prices_by_zone': pd.DataFrame()  # Time_series_price
            }
        
        self.Clustering_information = {}

        self.VarPrice = False
        self.OnlyGen = True
        self.CurtCost=False

        self.MixedBinCont = False
        self.TEP_n_years = 25
        self.TEP_discount_rate =0.02
        self.Array_opf = False
        
        self.name = 'Grid'
        
        if self.nodes_AC:
            self.Update_Graph_AC()
            self.Update_PQ_AC()
           
        if self.nodes_DC:
            self.Update_Graph_DC()
            self.Update_P_DC()
        else:
            self.Num_Grids_DC=0
        # #Call Y bus formula to fill matrix
        self.create_Ybus_AC()
        self.create_Ybus_DC()
        
        
        self.Generators =[]
        self.Generators_DC =[]
        
        self.RenSource_zones=[]
        self.RenSource_zones_dic={}
        self.RenSources =[]
        self.rs2node = {'DC': {},
                        'AC': {}}

        self.renewable_types = list(Grid.DEFAULT_RENEWABLE_TYPES)
        self.gen_ac_types = list(Grid.DEFAULT_GENERATION_TYPES)
        self.gen_dc_types = list(Grid.DEFAULT_GENERATION_TYPES) #currently there is no difference between AC and DC generation types
        # Single source of truth for generation types.
        self.generation_types = list(dict.fromkeys(
                list(self.gen_ac_types) + list(self.renewable_types) + list(self.gen_dc_types)
                ))
        # Default per-type limits are derived from the type list.
        self.generation_type_limits = {gen_type: 1 for gen_type in self.generation_types}
        self.current_generation_type_limits = {gen_type: 1 for gen_type in self.generation_types}
        self.TEP_n_periods = None
                


        self.Time_series = []
        self.Time_series_dic ={}

        self.Price_Zones =[]
        self.Price_Zones_dic ={}
      
        self.Clusters ={}
        
    
        self.OPF_Price_Zones_constraints_used=False
        
   
        self.OWPP_node_to_ts={}
        # Node type differentiation
        
    def reset_run_flags(self):
        """
        Helper to clear run-type flags before starting a new analysis.
        Call this before setting one of OPF_run / TEP_run / MP_TEP_run to True.
        """
        self.OPF_run = False
        self.TEP_run = False
        self.MP_TEP_run = False
        
    @property
    def nodes_AC(self):
        return self._nodes_AC

    # Setter for AC nodes that updates the dictionary
    @nodes_AC.setter
    def nodes_AC(self, new_nodes_AC):
        self._nodes_AC = new_nodes_AC if new_nodes_AC is not None else []
        self._invalidate_node_caches()

    # Property for DC nodes
    @property
    def nodes_DC(self):
        return self._nodes_DC

    # Setter for DC nodes that updates the dictionary
    @nodes_DC.setter
    def nodes_DC(self, new_nodes_DC):
        self._nodes_DC = new_nodes_DC if new_nodes_DC is not None else []
        self._invalidate_DC_caches()  # Invalidate cache when nodes change
        
    # Property to return dictionary of AC nodes
    @property
    def nodes_dict_AC(self):
        if self._nodes_dict_AC is None:  # Rebuild if cache is invalid
            self._nodes_dict_AC = {node.name: idx for idx, node in enumerate(self._nodes_AC)}
        return self._nodes_dict_AC

    # Property to return dictionary of DC nodes
    @property
    def nodes_dict_DC(self):
        if self._nodes_dict_DC is None:  # Rebuild if cache is invalid
            self._nodes_dict_DC = {node.name: idx for idx, node in enumerate(self._nodes_DC)}
        return self._nodes_dict_DC

    # Method to extend AC nodes
    def extend_nodes_AC(self, new_nodes):
        self._nodes_AC.extend(new_nodes)
        self._invalidate_node_caches()  # Invalidate the cache

    # Method to remove an AC node
    def remove_nodes_AC(self, node):
        self._nodes_AC.remove(node)
        self._invalidate_node_caches()  # Invalidate the cache
        
    def _invalidate_node_caches(self):
        """Reset all cached node lists when nodes_AC changes."""
        self._pq_nodes = None
        self._pv_nodes = None
        self._slack_nodes = None
        self._nodes_dict_AC = None
        
    # Method to extend DC nodes
    def extend_nodes_DC(self, new_nodes):
        self._nodes_DC.extend(new_nodes)
        self._invalidate_DC_caches()  # Invalidate the cache

    # Method to remove a DC node
    def remove_nodes_DC(self, node):
        self._nodes_DC.remove(node)
        self._invalidate_DC_caches()  # Invalidate the cache    
        
    def _invalidate_DC_caches(self):
        """Reset all cached DC node lists when nodes_DC changes."""
        self._PAC_nodes = None
        self._P_nodes = None
        self._droop_nodes = None
        self._slackDC_nodes = None
        self._nodes_dict_DC = None        
    

    @property
    def n_ren(self):
        return len(self.RenSources) if self.RenSources is not None else 0
    
    @property
    def n_gen(self):
        return len(self.Generators) if self.Generators is not None else 0
    
    @property
    def n_gen_DC(self):
        return len(self.Generators_DC) if self.Generators_DC is not None else 0
    
    # AC grid properties
    @property
    def nn_AC(self):
        return len(self.nodes_AC) if self.nodes_AC is not None else 0  # Number of AC nodes
    
    @property
    def npq(self):
        return len(self.pq_nodes) if self.pq_nodes is not None else 0  # Number of PQ nodes
    
    @property
    def npv(self):
        return len(self.pv_nodes) if self.pv_nodes is not None else 0  # Number of PV nodes
    
    @property
    def pq_nodes(self):
        if self._pq_nodes is None:
            self._pq_nodes = [node for node in self._nodes_AC if node.type == 'PQ']
        return self._pq_nodes

    @property
    def pv_nodes(self):
        if self._pv_nodes is None:
            self._pv_nodes = [node for node in self._nodes_AC if node.type == 'PV']
        return self._pv_nodes

    @property
    def slack_nodes(self):
        if self._slack_nodes is None:
            self._slack_nodes = [node for node in self._nodes_AC if node.type == 'Slack']
        return self._slack_nodes
    
    @property
    def nl_AC(self):
        return len(self.lines_AC) if self.lines_AC is not None else 0   
    
    @property
    def nle_AC(self): 
        return len(self.lines_AC_exp) if self.lines_AC_exp is not None else 0   
    
    @property
    def nlr_AC(self): 
        return len(self.lines_AC_rec) if self.lines_AC_rec is not None else 0   
    
    @property
    def nct_AC(self):
        return len(self.lines_AC_ct) if self.lines_AC_ct is not None else 0   

    @property
    def nttf(self): 
        return len(self.lines_AC_tf) if self.lines_AC_tf is not None else 0     
    
    # DC grid properties
    @property
    def nn_DC(self):
        return len(self.nodes_DC) if self.nodes_DC is not None else 0  # Number of DC nodes
    
    @property
    def nPAC(self):
        return len(self.PAC_nodes) if self.PAC_nodes is not None else 0  # Number of PAC nodes
    
    @property
    def nP(self):
        return len(self.P_nodes) if self.P_nodes is not None else 0  # Number of P nodes
    
    @property
    def nDroop(self):
        return len(self.droop_nodes) if self.droop_nodes is not None else 0  # Number of droop nodes

    @property
    def PAC_nodes(self):
        if self._PAC_nodes is None:
            self._PAC_nodes = [node for node in self._nodes_DC if node.type == 'PAC']
        return self._PAC_nodes

    @property
    def P_nodes(self):
        if self._P_nodes is None:
            self._P_nodes = [node for node in self._nodes_DC if node.type == 'P']
        return self._P_nodes

    @property
    def droop_nodes(self):
        if self._droop_nodes is None:
            self._droop_nodes = [node for node in self._nodes_DC if node.type == 'Droop']
        return self._droop_nodes

    @property
    def slackDC_nodes(self):
        if self._slackDC_nodes is None:
            self._slackDC_nodes = [node for node in self._nodes_DC if node.type == 'Slack']
        return self._slackDC_nodes  

    @property
    def nl_DC(self):
        return len(self.lines_DC) if self.lines_DC is not None else 0   
       
    @property
    def ncfc_DC(self):
        return len(self.CFC_DC) if self.CFC_DC is not None else 0  # Number of Current Flow Controller

    
    @property
    def ncdc_DC(self):
        return len(self.Converters_DCDC) if self.Converters_DCDC is not None else 0  # Number of DC-DC converters

    # ACDC Converter properties
    @property
    def nconv(self):
        return len(self.Converters_ACDC) if self.Converters_ACDC is not None else 0  # Number of converters
    
    @property
    def nconvP(self):
        return len(self.P_Conv) if self.P_Conv is not None else 0  # Number of P converters
    
    @property
    def nconvD(self):
        return len(self.Droop_Conv) if self.Droop_Conv is not None else 0  # Number of Droop converters
    
    @property
    def nconvS(self):
        return len(self.Slack_Conv) if self.Slack_Conv is not None else 0  # Number of Slack converters


    @property
    def P_Conv(self):
        P_Conv = [conv for conv in self.Converters_ACDC if conv.type == 'P']
        return P_Conv

    @property
    def Slack_Conv(self):
        Slack_Conv = [
            conv for conv in self.Converters_ACDC if conv.type == 'Slack']
        return Slack_Conv

    @property
    def Droop_Conv(self):
        Droop_Conv = [
            conv for conv in self.Converters_ACDC if conv.type == 'Droop']
        return Droop_Conv
    
    
    def check_stand_alone_is_slack(self):
        for node in self.nodes_AC:
            if node.stand_alone:
                node.type = 'Slack'
        
    
    def Update_Graph_DC(self):
        self.Graph_DC = nx.Graph()

        "Checking for un used nodes "
        used_nodes = set()

        # Iterate through lines
        for line in self.lines_DC:
            used_nodes.add(line.toNode)
            used_nodes.add(line.fromNode)

        # Iterate through converters

        if self.Converters_ACDC != None:
            for converter in self.Converters_ACDC:
                used_nodes.add(converter.Node_DC)

        # Filter out unused nodes
        nodes = [node for node in self.nodes_DC if node in used_nodes]

        for node in nodes:
            self.node_positions[node]=(node.x_coord,node.y_coord)
            
            if node in used_nodes:
                node.used = True

        self.Graph_DC_unused_nodes = [node for node in self.nodes_DC if not node.used]

        for line in self.lines_DC:
            self.Graph_toPlot.add_edge(line.fromNode, line.toNode, line=line)
            self.Graph_DC.add_edge(line.fromNode, line.toNode,line=line)
            line.toNode.stand_alone = False
            line.fromNode.stand_alone = False

        for node in self.nodes_DC:
            if node.stand_alone:
                self.Graph_DC.add_node(node)
                
        self.Grids_DC = list(nx.connected_components(self.Graph_DC))
        self.Num_Grids_DC = len(self.Grids_DC)
        self.Graph_node_to_Grid_index_DC = {}
        self.Graph_line_to_Grid_index_DC = {}
        self.Graph_grid_to_MTDC={}
        
        self.load_grid_DC=np.zeros(self.Num_Grids_DC)
        self.rating_grid_DC=np.zeros(self.Num_Grids_DC)
        self.Graph_number_lines_DC=np.zeros(self.Num_Grids_DC)

        self.Graph_kV_base = np.zeros(self.Num_Grids_DC)
        self.num_MTDC=0
        self.MTDC = {} 
        
        for i, Grid in enumerate(self.Grids_DC):
            for node in Grid:
                self.Graph_node_to_Grid_index_DC[node.nodeNumber] = i
                for line in self.lines_DC:
                    if line.fromNode == node or line.toNode == node:
                        self.Graph_line_to_Grid_index_DC[line] = i
                        self.Graph_kV_base[i] = line.kV_base
        for line in self.lines_DC:
            g=self.Graph_line_to_Grid_index_DC[line]
            self.Graph_number_lines_DC[g]+=1
            self.rating_grid_DC[g]+=line.MW_rating
            
                
        self.num_slackDC = np.zeros(self.Num_Grids_DC)
        for i in range(self.Num_Grids_DC):
            if self.Graph_number_lines_DC[i] >=2:
                self.MTDC[self.num_MTDC]=i
                self.Graph_grid_to_MTDC[i]=self.num_MTDC
                self.num_MTDC+=1
            for node in self.Grids_DC[i]:
                if node.type == 'Slack':
                    self.num_slackDC[i] += 1

            s = 1
            if self.num_slackDC[i] == 0:
                print(
                    f'For Grid DC {i+1} no slack bus found, results may not be accurate')

            if self.num_slackDC[i] > 1:
                print(f'For Grid DC {i+1} more than one slack bus found, results may not be accurate')
            
         
        s = 1

   
    def Update_Graph_AC(self):
        self.Graph_AC = nx.MultiGraph()
        

        "Checking for un used nodes "
        used_nodes = set()

        # Iterate through lines
        for line in self.lines_AC:
            used_nodes.add(line.toNode)
            used_nodes.add(line.fromNode)

        # Iterate through converters
        if self.Converters_ACDC != None:

            for converter in self.Converters_ACDC:
                used_nodes.add(converter.Node_AC)
                self.Graph_toPlot.add_node(converter.Node_AC) 

        # Filter out unused nodes
        nodes = [node for node in self.nodes_AC if node in used_nodes]

        for node in nodes:
            self.node_positions[node]=(node.x_coord,node.y_coord)
            
            if node in used_nodes:
                node.used = True

        self.Graph_AC_unused_nodes = [
            node for node in self.nodes_AC if not node.used]

        s = 1

    
        "Creating Graphs to differentiate Grids"
        for line in self.lines_AC + self.lines_AC_exp + self.lines_AC_rec + self.lines_AC_tf + self.lines_AC_ct:
            self.Graph_AC.add_edge(line.fromNode, line.toNode,line=line)
            self.Graph_toPlot.add_edge(line.fromNode, line.toNode,line=line)
            line.toNode.stand_alone = False
            line.fromNode.stand_alone = False

        for node in self.nodes_AC:
            if node.stand_alone:
                self.Graph_AC.add_node(node)
                   
            
        self.Grids_AC = list(nx.connected_components(self.Graph_AC))
        self.Num_Grids_AC = len(self.Grids_AC)
        self.Graph_node_to_Grid_index_AC = {}
        self.Graph_line_to_Grid_index_AC = {}
        self.load_grid_AC=np.zeros(self.Num_Grids_AC)
        self.rating_grid_AC=np.zeros(self.Num_Grids_AC)
        self.Graph_number_lines_AC=np.zeros(self.Num_Grids_AC)

        for i, Grid in enumerate(self.Grids_AC):
            for node in Grid:
                self.Graph_node_to_Grid_index_AC[node.nodeNumber] = i
                for line in self.lines_AC + self.lines_AC_exp + self.lines_AC_rec + self.lines_AC_tf + self.lines_AC_ct:
                    if line.fromNode == node or line.toNode == node:
                        self.Graph_line_to_Grid_index_AC[line] = i
        

        for line in self.lines_AC + self.lines_AC_exp + self.lines_AC_rec + self.lines_AC_tf + self.lines_AC_ct:
            g=self.Graph_line_to_Grid_index_AC[line]
            self.rating_grid_AC[g]+=line.capacity_MVA
            self.Graph_number_lines_AC[g]+=1
            
        "Slack identification"
        self.num_slackAC = np.zeros(self.Num_Grids_AC)

        for i in range(self.Num_Grids_AC):

            for node in self.Grids_AC[i]:
                if node.type == 'Slack':
                    self.num_slackAC[i] += 1
            if self.num_slackAC[i] == 0 and self.lines_AC != []:
                print(f'For Grid AC {i+1} no slack bus found.')
                print(f'Please set one before any calculations')
                # sys.exit()
            if self.num_slackAC[i] > 1:
                print(
                    f'For Grid AC {i+1} more than one slack bus found, results may not be accurate')
        
        
        s = 1
        
    def get_linesAC_by_node(self, nodeNumber):
        lines = [line for line in self.lines_AC if
                 (line.toNode.nodeNumber == nodeNumber or line.fromNode.nodeNumber == nodeNumber)]
        return lines

    def get_linesDC_by_node(self, nodeNumber):
        lines = [line for line in self.lines_DC if
                 (line.toNode.nodeNumber == nodeNumber or line.fromNode.nodeNumber == nodeNumber)]
        return lines

    def get_lineDC_by_nodes(self, fromNode, toNode):
        lines = [line for line in self.lines_DC if
                 (line.toNode.nodeNumber == fromNode and line.fromNode.nodeNumber == toNode) or
                 (line.toNode.nodeNumber == toNode and line.fromNode.nodeNumber == fromNode)]
        return lines[0] if lines else None

    
    def Update_P_DC(self):

        self.P_DC = np.vstack([node.PGi-node.PLi
                               +node.PconvDC
                               +sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                               +sum(gen.PGen for gen in node.connected_gen)
                                for node in self.nodes_DC])
        self.Pconv_DC = np.vstack([node.Pconv for node in self.nodes_DC])
        
        s=1
    def Update_PQ_AC(self):
        for node in self.nodes_AC:
            node.Q_s_fx=sum(self.Converters_ACDC[conv].Q_AC for conv  in node.connected_conv if self.Converters_ACDC[conv].AC_type=='PQ')
            node.Q_s   = sum(self.Converters_ACDC[conv].Q_AC for conv  in node.connected_conv if self.Converters_ACDC[conv].AC_type!='PQ')
        # # Negative means power leaving the system, positive means injected into the system at a node  
       
        self.P_AC = np.vstack([node.PGi
                               +sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                               +sum(gen.PGen for gen in node.connected_gen)
                               -node.PLi for node in self.nodes_AC])
        self.Q_AC = np.vstack([node.QGi+sum(gen.QGen for gen in node.connected_gen)
                               -node.QLi +node.Q_s_fx for node in self.nodes_AC])
        self.Ps_AC = np.vstack([node.P_s for node in self.nodes_AC])
        self.Qs_AC = np.vstack([node.Q_s for node in self.nodes_AC])

        s = 1

    def create_Ybus_AC(self):
        
        self.Ybus_AC = np.zeros((self.nn_AC, self.nn_AC), dtype=complex)
        self.AdmitanceVec_AC = np.zeros((self.nn_AC), dtype=complex)
        Ybus_nn= np.zeros((self.nn_AC),dtype=complex)
        # off diagonal elements
        for k in range(self.nl_AC):
            line = self.lines_AC[k]
            fromNode = line.fromNode.nodeNumber
            toNode = line.toNode.nodeNumber

            
            branch_ff = line.Ybus_branch[0, 0]
            branch_ft = line.Ybus_branch[0, 1]
            branch_tf = line.Ybus_branch[1, 0]
            branch_tt = line.Ybus_branch[1, 1]
            
            
            self.Ybus_AC[toNode, fromNode]+=branch_tf
            self.Ybus_AC[fromNode, toNode]+=branch_ft
            
            self.AdmitanceVec_AC[fromNode] += line.Y/2
            self.AdmitanceVec_AC[toNode] += line.Y/2
            
            Ybus_nn[fromNode] += branch_ff
            Ybus_nn[toNode] += branch_tt


        self.Ybus_AC_full = np.copy(self.Ybus_AC)    
        Ybus_nn_full = np.copy(Ybus_nn)

        for k in range(self.nle_AC):
            line = self.lines_AC_exp[k]
            fromNode = line.fromNode.nodeNumber
            toNode = line.toNode.nodeNumber

            branch_ff = line.Ybus_branch[0, 0]*line.np_line
            branch_ft = line.Ybus_branch[0, 1]*line.np_line
            branch_tf = line.Ybus_branch[1, 0]*line.np_line
            branch_tt = line.Ybus_branch[1, 1]*line.np_line

            self.Ybus_AC_full[toNode, fromNode]+=branch_tf
            self.Ybus_AC_full[fromNode, toNode]+=branch_ft
            
            
            Ybus_nn_full[fromNode] += branch_ff
            Ybus_nn_full[toNode] += branch_tt

        for k in range(self.nlr_AC):
            line = self.lines_AC_rec[k]
            fromNode = line.fromNode.nodeNumber
            toNode = line.toNode.nodeNumber

            if line.rec_branch:
                branch_ff = line.Ybus_branch_new[0, 0]
                branch_ft = line.Ybus_branch_new[0, 1]
                branch_tf = line.Ybus_branch_new[1, 0]
                branch_tt = line.Ybus_branch_new[1, 1]
            else:    
                branch_ff = line.Ybus_branch[0, 0]
                branch_ft = line.Ybus_branch[0, 1]
                branch_tf = line.Ybus_branch[1, 0]
                branch_tt = line.Ybus_branch[1, 1]

            self.Ybus_AC_full[toNode, fromNode]+=branch_tf
            self.Ybus_AC_full[fromNode, toNode]+=branch_ft
            
            
            Ybus_nn_full[fromNode] += branch_ff
            Ybus_nn_full[toNode] += branch_tt


        for k in range(self.nct_AC):
            line = self.lines_AC_ct[k]
            fromNode = line.fromNode.nodeNumber
            toNode = line.toNode.nodeNumber
            if line.active_config >=0:
                branch_ff = line.Ybus_list[line.active_config][0, 0]
                branch_ft = line.Ybus_list[line.active_config][0, 1]
                branch_tf = line.Ybus_list[line.active_config][1, 0]
                branch_tt = line.Ybus_list[line.active_config][1, 1]

                self.Ybus_AC_full[toNode, fromNode]+=branch_tf
                self.Ybus_AC_full[fromNode, toNode]+=branch_ft
                
                
                Ybus_nn_full[fromNode] += branch_ff
                Ybus_nn_full[toNode] += branch_tt
            
        for m in range(self.nn_AC):
            node = self.nodes_AC[m]

            self.AdmitanceVec_AC[m] += node.Reactor
            Ybus_nn[m] += node.Reactor
            Ybus_nn_full[m] += node.Reactor

            self.Ybus_AC[m, m] = Ybus_nn[m]
            self.Ybus_AC_full[m, m] = Ybus_nn_full[m]
            
    def create_Ybus_DC(self):
        self.Ybus_DC = np.zeros((self.nn_DC, self.nn_DC), dtype=float)
        self.Ybus_DC_full = np.zeros((self.nn_DC, self.nn_DC), dtype=float)
        # off diagonal elements
        for k in range(self.nl_DC):
            line = self.lines_DC[k]
            fromNode = line.fromNode.nodeNumber
            toNode = line.toNode.nodeNumber
            if line.R ==0:
                s=1
            self.Ybus_DC[fromNode, toNode] -= line.np_line/line.R
            self.Ybus_DC[toNode, fromNode] = self.Ybus_DC[fromNode, toNode]
            self.Ybus_DC_full[fromNode, toNode] -= line.np_line*line.pol/line.R
            self.Ybus_DC_full[toNode, fromNode] = self.Ybus_DC_full[fromNode, toNode]

        # Diagonal elements
        for m in range(self.nn_DC):
            self.Ybus_DC[m, m] = -self.Ybus_DC[:,m].sum() if self.Ybus_DC[:, m].sum() != 0 else 1.0
            self.Ybus_DC_full[m, m] = -self.Ybus_DC_full[:,m].sum() if self.Ybus_DC_full[:, m].sum() != 0 else 1.0

    def Check_SlacknDroop(self, change_slack2Droop):
        for conv in self.Converters_ACDC:
            if conv.type == 'Slack':

                DC_node = conv.Node_DC

                node_count = 0

                P_syst = 0
                for conv_other in self.Converters_ACDC:
                    DC_node_other = conv_other.Node_DC
                    connected = nx.has_path(
                        self.Graph_DC, DC_node, DC_node_other)
                    if connected == True:
                        P_syst += -conv_other.P_DC
                    else:
                        # print(f"Nodes {DC_node.name} and {DC_node_other.name} are not connected.")
                        node_count += 1

                if change_slack2Droop == True:
                    if self.nn_DC-node_count != 2:

                        conv.type = 'Droop'
                        DC_node.type = 'Droop'
                conv.P_DC = P_syst
                DC_node.Pconv = P_syst

                self.Update_P_DC()

            elif conv.type == 'Droop':

                DC_node = conv.Node_DC

                node_count = 0

                for conv_other in self.Converters_ACDC:
                    DC_node_other = conv_other.Node_DC
                    connected = nx.has_path(self.Graph_DC, DC_node, DC_node_other)
                    if connected == False:
                        node_count += 1

                if self.nn_DC-node_count == 2:
                    g=self.Graph_node_to_Grid_index_DC[DC_node.nodeNumber]
                    
                    if any(node.type == 'Slack' for node in self.Grids_DC[g]):
                        s=1
                    else:
                        conv.type = 'Slack'
                        DC_node.type = 'Slack'
                        print(f"Changing converter {conv.name} to Slack")
                self.Update_P_DC()

    

    def Line_AC_calc(self):
        V_cart = self._initialize_voltage_cartesian()
        
        self.I_AC_cart = np.matmul(self.Ybus_AC, V_cart)
        self.I_AC_m = abs(self.I_AC_cart)
        self.I_AC_th = np.angle(self.I_AC_cart)

  
        for line in self.lines_AC:
            self._calculate_line_power_flow(line, V_cart)

    def Line_AC_calc_exp(self):
        """
        Calculate power flow and losses for expansion AC lines, reconductored lines, 
        and configurable transmission lines.
        
        This method processes three types of AC lines:
        - lines_AC_exp: Expansion lines with parallel circuits
        - lines_AC_rec: Reconductored lines with new parameters
        - lines_AC_ct: Configurable transmission lines with multiple configurations
        """
        V_cart = self._initialize_voltage_cartesian()
        
        for line in self.lines_AC_exp:
            self._calculate_line_power_flow(line, V_cart, use_parallel=True)
            
        # Process reconductored lines
        for line in self.lines_AC_rec:
            self._calculate_line_power_flow(line, V_cart, use_reconductored=True)
            
        # Process configurable transmission lines
        for line in self.lines_AC_ct:
            if line.active_config >=0:
              self._calculate_line_power_flow(line, V_cart, use_configurable=True)
    
    def _initialize_voltage_cartesian(self):
        """
        Initialize voltage arrays and convert to cartesian form.
        
        Returns
        -------
        ndarray
            Complex voltage vector in cartesian form
        """
        try: 
            V_cart = pol2cartz(self.V_AC, self.Theta_V_AC)
        except (ValueError, AttributeError) as e:
            # Initialize voltage arrays if not available
            self.V_AC = np.zeros(self.nn_AC)
            self.Theta_V_AC = np.zeros(self.nn_AC)
            for node in self.nodes_AC: 
                nAC = node.nodeNumber
                self.V_AC[nAC] = node.V
                self.Theta_V_AC[nAC] = node.theta
            V_cart = pol2cartz(self.V_AC, self.Theta_V_AC)
        return V_cart
    
    def _calculate_line_power_flow(self, line, V_cart, use_parallel=False, 
                                 use_reconductored=False, use_configurable=False):
        """
        Calculate power flow and losses for a single AC line.
        
        Parameters
        ----------
        line : Line_AC
            The line to calculate power flow for
        V_cart : ndarray
            Complex voltage vector in cartesian form
        use_parallel : bool
            Whether to use parallel circuit factor (np_line)
        use_reconductored : bool
            Whether to use new Ybus parameters for reconductored lines
        use_configurable : bool
            Whether to use active configuration Ybus for configurable lines
        """
        i = line.fromNode.nodeNumber
        j = line.toNode.nodeNumber
        
        # Select appropriate Ybus matrix
        if use_reconductored and line.rec_branch:
            Ybus = line.Ybus_branch_new
        elif use_configurable:
            Ybus = line.Ybus_list[line.active_config]
        else:
            Ybus = line.Ybus_branch
        
        # Calculate currents
        if use_parallel:
            # Apply parallel circuit factor
            i_from = line.np_line * (Ybus[0, 0] * V_cart[i] + Ybus[0, 1] * V_cart[j])
            i_to = line.np_line * (Ybus[1, 0] * V_cart[i] + Ybus[1, 1] * V_cart[j])
        else:
            i_from = Ybus[0, 0] * V_cart[i] + Ybus[0, 1] * V_cart[j]
            i_to = Ybus[1, 0] * V_cart[i] + Ybus[1, 1] * V_cart[j]
        
        # Calculate power flows
        Sfrom = V_cart[i] * np.conj(i_from)
        Sto = V_cart[j] * np.conj(i_to)
        
        # Calculate losses
        line.loss = Sfrom + Sto
        line.P_loss = np.real(line.loss)
        
        # Store results
        line.fromS = Sfrom
        line.toS = Sto
        line.i_from, _ = cartz2pol(i_from)
        line.i_to, _ = cartz2pol(i_to)

    def Line_DC_calc(self):
        V = self.V_DC
        Ybus = self.Ybus_DC
        
        # self.I_DC = np.matmul(Ybus, V)

        Iij = np.zeros((self.nn_DC, self.nn_DC), dtype=float)
        Pij_DC = np.zeros((self.nn_DC, self.nn_DC), dtype=float)

        s = 1
        for line in self.lines_DC:
            i = line.fromNode.nodeNumber
            j = line.toNode.nodeNumber
            pol = line.pol

            Iij[i, j] = (V[i]-V[j])*-Ybus[i, j]
            Iij[j, i] = (V[j]-V[i])*-Ybus[i, j]

            Pij_DC[i, j] = V[i]*(Iij[i, j])*pol
            Pij_DC[j, i] = V[j]*(Iij[j, i])*pol
            
            line.toP=Pij_DC[j,i]*line.np_line
            line.fromP=Pij_DC[i,j]*line.np_line

        L_loss = np.zeros(self.nl_DC, dtype=float)

        for line in self.lines_DC:
            l = line.lineNumber
            i = line.fromNode.nodeNumber
            j = line.toNode.nodeNumber

            L_loss[l] = (Pij_DC[i, j]+Pij_DC[j, i])*line.np_line
            line.loss = (Pij_DC[i, j]+Pij_DC[j, i])*line.np_line

        self.L_loss_DC = L_loss

        self.Pij_DC = Pij_DC

        self.Iij_DC = Iij
        s = 1

        
        
class Gen_AC:
    genNumber =0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.genNumber = 0
        cls.names = set()
             
    @property
    def name(self):
        return self._name

    @property
    def S_base(self):
        return self._S_base
    
    @property
    def life_time_hours(self):
        return self.life_time *8760

    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        
        old_S_base = getattr(self, "_S_base", None)
        if old_S_base is not None and old_S_base != new_S_base:
                rate = old_S_base / new_S_base
                self.Max_pow_gen *= rate
                self.Max_pow_genR *= rate
                self.Min_pow_gen *= rate
                self.Min_pow_genR *= rate
                self.PGen *= rate
                self.QGen *= rate
                self.Pset *= rate
                self.Qset *= rate
                self.Max_S *= rate
        self._S_base = new_S_base
    
    @property
    def capacity_MVA(self):
        maxMVAR = max(abs(self.Max_pow_genR),abs(self.Min_pow_genR))
        if self.Max_S is not None:
            return self.Max_S *self.S_base
        elif self.Max_pow_gen >0:
            return (self.Max_pow_gen**2+maxMVAR**2)**0.5*self.S_base
        else:
            return maxMVAR*self.S_base
    
    @property
    def loading(self):
        return self.apparent_MVA/(self.capacity_MVA*self.np_gen)*100 if self.np_gen >0 else 0
    @property
    def apparent_MVA(self):
        return max(abs(self.PGen), abs(self.QGen)) * self.S_base


    def __init__(self,name, node,Max_pow_gen: float,Min_pow_gen: float,Max_pow_genR: float,Min_pow_genR: float,quadratic_cost_factor: float=0,linear_cost_factor: float=0,fixed_cost:float =0,Pset:float=0,Qset:float=0,S_rated:float=None,gen_type='Other',installation_cost:float=0,S_base:float=100):
        self.genNumber = Gen_AC.genNumber
        Gen_AC.genNumber += 1
        self.S_base = S_base
        self.S_base_i = S_base
        
        self.Node_AC=node.name
        self.x_coord = node.x_coord
        self.y_coord = node.y_coord
        self.geometry= node.geometry
        self.kV_base = node.kV_base
        self.PZ = node.PZ
        self.hover_text = None
        self.gen_type=gen_type
        self.Max_pow_gen=Max_pow_gen
        self.Min_pow_gen=Min_pow_gen
        self.Max_pow_genR=Max_pow_genR
        self.Min_pow_genR=Min_pow_genR

        self.Max_S= S_rated
        
        node.S_rating += self.capacity_MVA
        
        #Variable to activate or deactivate the generator in the OPF
        self.activate_gen_opf = False
        self.gen_active = 1

        #Variable to have a variable number of generators in the TEP
        self.np_gen_opf = False
        self.np_gen_mp = False  # Multi-period TEP: submodel np_gen driven by master (full bounds)

        self.np_gen_i = 1
        self.np_gen_b = 1
        self.np_gen = 1
        self.np_gen_max=3   # maximum number of generators to be present at the same time
        
        # Used in multi period TEP
        self.investment_decisions = {
            'planned_installation': [0],
            'planned_decomision': [0],
            'max_inv': [self.np_gen_max],
            'np_dynamic': [self.np_gen]
        }
        

        self.lf=linear_cost_factor
        self.qf=quadratic_cost_factor
        self.fc=fixed_cost

        self.life_time = 50
        self.base_cost = installation_cost
        
        if S_rated is not None:
            self.cost_perMVA = installation_cost/S_rated
        elif Max_pow_gen >0:
            self.cost_perMVA = installation_cost/Max_pow_gen
        else:
            Q_rate = max (abs(Min_pow_genR),abs(Max_pow_genR))
            self.cost_perMVA = installation_cost/Q_rate
            
            
        self.price_zone_link = False
        
        node.connected_gen.append(self)
        
        self.PGen=Pset
        self.QGen=Qset
        
        self.Pset=Pset
        self.Qset=Qset
        
        if name in Gen_AC.names:
            count = 1
            new_name = f"{name}_{count}"
            
            while new_name in Gen_AC.names:
                count += 1
                new_name = f"{name}_{count}"
            name = new_name
        if name is None:
            self._name = str(node.name)
        else:
            self._name = name

        Gen_AC.names.add(self.name)
        
       
class Gen_DC:
    genNumber_DC =0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.genNumber_DC = 0
        cls.names = set()
             
    @property
    def name(self):
        return self._name

    @property
    def S_base(self):
        return self._S_base
    
    @property
    def life_time_hours(self):
        return self.life_time *8760

    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        
        old_S_base = getattr(self, "_S_base", None)
        if old_S_base is not None and old_S_base != new_S_base:  
                rate = old_S_base / new_S_base
                self.Max_pow_gen *= rate
                self.PGen *= rate
                self.Pset *= rate
        self._S_base = new_S_base
    @property
    def capacity_MW(self):
        return self.Max_pow_gen*self.S_base
    
    @property
    def loading(self):
        return self.PGen/(self.capacity_MW*self.np_gen)*100 if self.np_gen >0 else 0
   

    def __init__(self,name, node,Max_pow_gen: float,Min_pow_gen: float,quadratic_cost_factor: float=0,linear_cost_factor: float=0,fixed_cost:float =0,Pset:float=0,gen_type='Other',installation_cost:float=0,S_base:float=100):
        self.genNumber_DC = Gen_DC.genNumber_DC
        Gen_DC.genNumber_DC += 1

        self.S_base = S_base
        self.S_base_i = S_base

        self.Node_DC=node.name
        self.x_coord = node.x_coord
        self.y_coord = node.y_coord
        self.geometry= node.geometry
        self.kV_base = node.kV_base
        self.PZ = node.PZ
        self.hover_text = None
        self.gen_type=gen_type
        self.Max_pow_gen=Max_pow_gen
        self.Min_pow_gen=Min_pow_gen
      

        #Variable to have a variable number of generators in the TEP
        self.np_gen_opf = False

        self.np_gen_i = 1
        self.np_gen_b = 1
        self.np_gen = 1
        self.np_gen_max=3
        
        self.lf=linear_cost_factor
        self.qf=quadratic_cost_factor
        self.fc=fixed_cost

        self.life_time = 50
        self.base_cost = installation_cost
       
        self.price_zone_link = False
        
        node.connected_gen.append(self)
        
        self.PGen=Pset
       
        self.Pset=Pset
       
        
        if name in Gen_DC.names:
            count = 1
            new_name = f"{name}_{count}"
            
            while new_name in Gen_DC.names:
                count += 1
                new_name = f"{name}_{count}"
            name = new_name
        if name is None:
            self._name = str(node.name)
        else:
            self._name = name

        Gen_DC.names.add(self.name)
            
class Ren_Source:
    rsNumber =0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.rsNumber = 0
        cls.names = set()
             
    @property
    def name(self):
        return self._name

    @property
    def S_base(self):
        return self._S_base
    
    @property
    def life_time_hours(self):
        return self.life_time *8760

    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        old_S_base = getattr(self, "_S_base", None)
        if old_S_base is not None and old_S_base != new_S_base:  
            rate = old_S_base / new_S_base
            self.Max_S *= rate
            self.PGi_ren_base *= rate
            self.QGi_ren *= rate
            self.Qmin *= rate
            self.Qmax *= rate
        self._S_base = new_S_base
    
    @property
    def capacity_MVA(self):
       
        return self.Max_S*self.S_base
    
    @property
    def loading(self):
        return self.apparent_MVA/(self.capacity_MVA*self.np_rsgen)*100 if self.np_rsgen >0 else 0
    @property
    def apparent_MVA(self):
        return max(abs(self.PGen), abs(self.QGen)) * self.S_base
    
    def __init__(self,name,node,PGi_ren_base: float,rs_type='Wind',S_base:float=100,installation_cost:float=0,Max_S_factor:float=1):
        self.rsNumber = Ren_Source.rsNumber
        Ren_Source.rsNumber += 1
        
        self.connected= 'AC'
        self.rs_type = rs_type
        
        self.curtailable= True
       
        self.life_time = 50
        self._S_base = S_base
        self.S_base_i = S_base
        
        self.Node=node.name
        self.x_coord = node.x_coord
        self.y_coord = node.y_coord

        node.S_rating += PGi_ren_base
        
        self.geometry= node.geometry
        self.kV_base = node.kV_base
        self.PZ = node.PZ
        
        
        self.PGi_ren = 0 
        self._PGi_ren_base=PGi_ren_base
        self._PRGi_available=1
        #self._PRGi_inv_factor =1
        

        #Variable to have a variable number of generators in the TEP
        self.np_rsgen_opf = False
        self.np_rsgen_mp = False  # Multi-period TEP: submodel np_rsgen driven by master (full bounds)

        self.np_rsgen_i = 1
        self.np_rsgen_b = 1
        self.np_rsgen = 1
        self.np_rsgen_max=3   # maximum number of generators to be present at the same time

        # Used in multi period TEP
        self.investment_decisions = {
            'planned_installation': [0],
            'planned_decomision': [0],
            'max_inv': [self.np_rsgen_max],
            'np_dynamic': [self.np_rsgen]
        }

        self.base_cost = installation_cost

        self.TS_dict = {
            'PRGi_available': None
        }
        
        self.inv_dic ={
            'PRGi_base' : None
        }

        self.PGRi_linked=False
        self.Ren_source_zone=None
        
        self.gamma = 1
        self.min_gamma = 0.0
        self.sigma=1.05
        
        self.QGi_ren = 0
        self.Qmax=0
        self.Qmin=0
        
        self.Max_S= PGi_ren_base*Max_S_factor

        if Max_S_factor is not None:
            self.cost_perMVA = installation_cost/PGi_ren_base*Max_S_factor*S_base
            
        node.connected_RenSource.append(self)
        node.RenSource=True
        
        self.update_PGi_ren()
        
        if name in Ren_Source.names:
            count = 1
            new_name = f"{name}_{count}"
            
            while new_name in Ren_Source.names:
                count += 1
                new_name = f"{name}_{count}"
            name = new_name
        if name is None:
            self._name = str(self.Node.name)
        else:
            self._name = name

        Ren_Source.names.add(self.name)
        
        self.hover_text = None
    
    @property
    def PGi_ren_base(self):
        return self._PGi_ren_base
    
    @PGi_ren_base.setter
    def PGi_ren_base(self, value):
        self._PGi_ren_base = value
        self.update_PGi_ren()

    #@property
    #def PRGi_inv_factor(self):
    #    return self._PRGi_inv_factor
    
    #@PRGi_inv_factor.setter
    #def PRGi_inv_factor(self, value):
    #    self._PRGi_inv_factor = value
    #    self.update_PGi_ren()

    @property
    def PRGi_available(self):
        return self._PRGi_available

    @PRGi_available.setter
    def PRGi_available(self, value):
        self._PRGi_available = value
        self.update_PGi_ren()
     
    def update_PGi_ren(self):
        self.PGi_ren = self._PGi_ren_base * self._PRGi_available #* self._PRGi_inv_factor
   
    
class Node_AC:  
    """
    Attributes
    ----------
    node_type : str
        Node type ('Slack' or 'PQ' or 'PV')
    Voltage_0 : float
        Initial voltage magnitude in pu
    theta_0 : float
        Initial voltage angle in radians
    kV_base : float
        Base voltage in kV
    Power_Gained : float
        Active power injection in pu
    Reactive_Gained : float
        Reactive power injection in pu
    Power_load : float
        Active power demand in pu
    Reactive_load : float
        Reactive power demand in pu
    Umin : float
        Minimum voltage magnitude in p.u.
    Umax : float
        Maximum voltage magnitude in p.u.
    Gs : float
        Shunt conductance in p.u.
    Bs : float
        Shunt susceptance in p.u.
    x_coord : float
        x-coordinate, preferably in longitude decimal format
    y_coord : float
        y-coordinate, preferably in latitude decimal format
    """    
    nodeNumber = 0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.nodeNumber = 0
        cls.names = set()
        
    @property
    def name(self):
        return self._name

    def __init__(self, node_type: str, Voltage_0: float, theta_0: float,kV_base:float, Power_Gained: float=0, Reactive_Gained: float=0, Power_load: float=0, Reactive_load: float=0, name=None, Umin=0.9, Umax=1.1,Gs:float= 0,Bs:float=0,x_coord=None,y_coord=None):
        
        self.nodeNumber = Node_AC.nodeNumber
        Node_AC.nodeNumber += 1
        self.type = node_type

        self.kV_base = kV_base
        self.V_ini = Voltage_0
        self.theta_ini = theta_0
        self.V = np.copy(self.V_ini)
        self.theta = np.copy(self.theta_ini)
        self.PGi = Power_Gained
        self.PGi_opt =0
        
        # self.PGi_ren_base=0
        self.PGi_ren= 0 
        # self._PRGi_available=1
        self.RenSource=False
        # self.PGRi_linked=False
        # self.Ren_source_zone=None
        self.S_rating = 0
        
        self.PLi= Power_load

        self._PLi_base = Power_load

        self.PLi_linked= False
        self._PLi_factor =1
        self._PLi_inv_factor=1
        
        self.TS_dict = {
            'Load' : None,
            'price': None,
            }
        
        self.inv_dic ={
            'Load' : None
        }
        self.investment_decisions = {
            'Load': []
        }
        
        self.QGi = Reactive_Gained
        self.QGi_opt =0
        self.QLi = Reactive_load
        
       

        self.Qmin = 0
        self.Qmax = 0
        self.Reactor = Gs+ Bs*1j
        # self.Q_max = Q_max
        # self.Q_min = Q_min
        # self.P_AC = self.PGi-self.PLi
        # self.Q_AC = self.QGi-self.QLi
        self.P_s = 0
        self.Q_s = 0
        self.Q_s_fx = 0  # reactive power by converters in PQ mode
        self.P_s_new = np.copy(self.P_s)
        self.used = False
        self.stand_alone = True
        
        self.P_INJ=Voltage_0
            
        self.price = 0.0
        self.Num_conv_connected=0
        self.connected_conv=set()
    

        #Used for turbine array optimisation
        self.ct_limit=None
        self.max_turbines_per_string=99
        self.pu_power_limit=None
        self.curtailment=1

        # self.Max_pow_gen=0
        # self.Min_pow_gen=0
        # self.Max_pow_genR=0
        # self.Min_pow_genR=0
        self.connected_gen=[]
        self.connected_RenSource=[]
        
        self.connected_toExpLine=[]
        self.connected_fromExpLine=[]
        
        self.connected_toRepLine=[]
        self.connected_fromRepLine=[]


        self.connected_toCTLine=[]
        self.connected_fromCTLine=[]

        self.connected_toTFLine=[]
        self.connected_fromTFLine=[]
        
        
        self.Umax= Umax
        self.Umin=Umin
        
        self.x_coord=x_coord
        self.y_coord=y_coord
        
        self.PZ = None
        self.hover_text = None
        self.geometry=None
        if name in Node_AC.names:
            Node_AC.nodeNumber -= 1
            raise NameError("Already used name '%s'." % name)
        if name is None:
            self._name = str(self.nodeNumber)
        else:
            self._name = name

        Node_AC.names.add(self.name)
  
    @property
    def PLi_base(self):
        return self._PLi_base
    
    @PLi_base.setter
    def PLi_base(self, value):
        self._PLi_base = value
        self.update_PLi()

    @property
    def PLi_factor(self):
        return self._PLi_factor

    @PLi_factor.setter
    def PLi_factor(self, value):
        self._PLi_factor = value
        self.update_PLi()        
    
    @property
    def PLi_inv_factor(self):
        return self._PLi_inv_factor
    
    @PLi_inv_factor.setter
    def PLi_inv_factor(self, value):
        self._PLi_inv_factor = value
        self.update_PLi()

    def update_PLi(self):
        self.PLi = self._PLi_base * self._PLi_factor * self._PLi_inv_factor
        
class Node_DC:
    """
    Attributes
    ----------
    node_type : str
        Node type ('Slack' or 'P' or 'Droop' or 'PAC')
    Voltage_0 : float
        Initial voltage magnitude in pu     
    Power_Gained : float
        Active power injection in pu
    Power_load : float
        Active power demand in pu
    kV_base : float
        Base voltage in kV
    Umin : float
        Minimum voltage magnitude in p.u.
    Umax : float
        Maximum voltage magnitude in p.u.
    x_coord : float
        x-coordinate, preferably in longitude decimal format
    y_coord : float
        y-coordinate, preferably in latitude decimal format
    """
    nodeNumber = 0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.nodeNumber = 0
        cls.names = set()
    
    @property
    def name(self):
        return self._name

    def __init__(self, node_type: str,kV_base:float, Voltage_0: float=1, Power_Gained: float=0, Power_load: float=0, name=None, Umin=0.95, Umax=1.05,x_coord=None,y_coord=None):
       
        self.nodeNumber = Node_DC.nodeNumber
        Node_DC.nodeNumber += 1

        self.V_ini = Voltage_0
        self.type = node_type
        self.kV_base = kV_base
        
        self.PGi = Power_Gained
        self.PLi_linked= False
        self.PLi= Power_load

        self._PLi_base = Power_load
        self._PLi_factor =1  # 0-1 value used for time series or scenario management
        self._PLi_inv_factor=1 # value used for investment period load increase
        
        self.S_rating = 0
        self.TS_dict = {
            'Load' : None,
            'price': None,
            }
        
        self.inv_dic ={
            'Load' : None
        }
        self.investment_decisions = {
            'Load': []
        }
        
        self.V = np.copy(self.V_ini)
        self.P_INJ = 0
        self.Pconv = 0
        
        self.used = False
        self.stand_alone=True
        
        self.PconvDC = 0
        self.connected_DCDC_to=set()
        self.connected_DCDC_from=set()
                
        self.price = 0.0
        
        self.Nconv= None
        self.Nconv_i=None
        self.ConvInv = False
        self.conv_loading=0
        self.conv_MW= 0
        
        self.Umax=Umax
        self.Umin=Umin
        
        self.x_coord=x_coord
        self.y_coord=y_coord
        
        self.PZ = None
        self.hover_text = None
        self.geometry=None

        self.connected_gen=[]
        self.connected_RenSource=[]
        
        
        if name in Node_DC.names:
            Node_DC.nodeNumber -= 1
            raise NameError("Already used name '%s'." % name)
        if name is None:
            self._name = str(self.nodeNumber)
        else:
            self._name = name

        Node_DC.names.add(self.name)

    @property
    def PLi_base(self):
        return self._PLi_base
    
    @PLi_base.setter
    def PLi_base(self, value):
        self._PLi_base = value
        self.update_PLi()

    @property
    def PLi_inv_factor(self):
        return self._PLi_inv_factor
    
    @PLi_inv_factor.setter
    def PLi_inv_factor(self, value):
        self._PLi_inv_factor = value
        self.update_PLi()

    @property
    def PLi_factor(self):
         return self._PLi_factor

    @PLi_factor.setter
    def PLi_factor(self, value):
         self._PLi_factor = value
         self.update_PLi()        
        
    def update_PLi(self):
         self.PLi = self._PLi_base * self._PLi_factor * self._PLi_inv_factor
         
class Line_AC:
    """
    Attributes
    ----------
    fromNode : Node_AC
        The starting node of the line
    toNode : Node_AC
        The ending node of the line
    r : float
        Resistance of the line in pu
    x : float
        Reactance of the line in pu
    g : float
        Conductance of the line in pu
    b : float
        Susceptance of the line in pu
    MVA_rating : float
        MVA rating of the line
    Length_km : float
        Length of the line in km
    m : float
        Number of conductors in the line
    shift : float
        Phase shift of the line in radians
    N_cables : int
        Number of cables in the line
    name : str
        Name of the line
    geometry : str
        Geometry of the line
    isTf : bool
        True if the line is a transformer, False otherwise
    S_base : float
        Base power of the line in MVA
    Cable_type : str
        Type of cable in the line
    
    """    
    lineNumber = 0
    names = set()
    _cable_database = None
    
    @classmethod
    def load_cable_database(cls, cable_database=None):
        """Load cable database from YAML files if not already loaded, or use provided DataFrame.
        
        Parameters
        ----------
        cable_database : pd.DataFrame, optional
            If provided, use this DataFrame as the cable database instead of loading from YAML files.
            The DataFrame should have cable names as index and cable specifications as columns.
            Only AC cables will be used (filtered by Type='AC' if Type column exists).
        """
        if cls._cable_database is None:
            if cable_database is not None:
                # Use provided DataFrame, but filter for AC cables if Type column exists
                if 'Type' in cable_database.columns:
                    type_norm = cable_database['Type'].astype(str).str.upper().replace({'HVAC': 'AC', 'HVDC': 'DC'})
                    cls._cable_database = cable_database[type_norm == 'AC'].copy()
                else:
                    # Assume all are AC if no Type column
                    cls._cable_database = cable_database.copy()
            else:
                # Load from YAML files
                # Get the path to the Cable_database directory
                module_dir = Path(__file__).parent
                cable_dir = module_dir / 'Cable_database'
                
                data_dict = {}
                # Read all YAML files in the directory
                for yaml_file in cable_dir.glob('*.yaml'):
                    with open(yaml_file, 'r', encoding='latin-1') as f:
                        cable_data = yaml.safe_load(f)
                        if cable_data:
                            # Each file has one cable
                            cable_name = list(cable_data.keys())[0]
                            specs = cable_data[cable_name]
                            
                            # Only include AC cables
                            typ = str(specs.get('Type', 'AC')).upper()
                            if typ in ('HVAC', 'AC'):
                                data_dict[cable_name] = specs
                
                if data_dict:
                    # Convert to pandas DataFrame
                    cls._cable_database = pd.DataFrame.from_dict(data_dict, orient='index')
                    #print(f"Loaded {len(data_dict)} AC cables into database")
                else:
                    print("No AC cable data found in any YAML files")

    @classmethod
    def reset_class(cls):
        cls.lineNumber = 0
        cls.names = set()
        
    @property
    def name(self):
        return self._name
    @property
    def apparent_MVA(self):
        return max(abs(self.fromS), abs(self.toS)) * self.S_base

    @property
    def capacity_MVA(self):
        return self.MVA_rating

    @property
    def loading(self):
        cap = self.capacity_MVA
        return 0.0 if cap == 0 else (self.apparent_MVA / cap) * 100.0 

    def remove(self):
        """Method to handle line removal from the class-level attributes."""
        Line_AC.lineNumber -= 1  # Decrement the line number counter
        Line_AC.names.remove(self._name)  # Remove the line's name from the set
        
    def get_cable_parameters(self, Cable_type, S_base, Length_km, N_cables,kV_base):
        from .grid_analysis import Cable_parameters
        """Get cable parameters from the database."""
        # Ensure database is loaded
        if Line_AC._cable_database is None:
            Line_AC.load_cable_database()
        Cable_type = Cable_type.replace(' ', '_')
        if Cable_type not in self._cable_database.index:
            raise ValueError(f"Cable type '{Cable_type}' not found in database")
        
        # Get cable data
        cable_data = self._cable_database.loc[Cable_type]
        
        # Calculate parameters
        R_Ohm = cable_data['R_Ohm_km'] 
        L_mH = cable_data['L_mH_km'] 
        C_uF = cable_data['C_uF_km'] 
        G_uS = cable_data['G_uS_km'] 
        A_rating = cable_data['A_rating']
      
        R,X,G,B,MVA_rating = Cable_parameters(S_base, R_Ohm, L_mH, C_uF, G_uS, A_rating, kV_base, Length_km,N_cables)
        return R, X, G, B, MVA_rating
    
    def __init__(self, fromNode: Node_AC, toNode: Node_AC,r: float= 0.001, x: float=0.001, g: float=0, b: float=0, MVA_rating: float=9999,Length_km:float=1.0,m:float=1, shift:float=0,N_cables=1, name=None,geometry=None,isTf=False,S_base:float=100,Cable_type:str ='Custom'):
        self.lineNumber = Line_AC.lineNumber
        Line_AC.lineNumber += 1
        
        self.S_base = S_base
        self.S_base_i = S_base
        self.Length_km = Length_km
        self.N_cables = N_cables

        self.fromNode = fromNode
        self.toNode = toNode
        self.kV_base = toNode.kV_base

        self.R = r
        self.X = x
        self.G = g
        self.B = b
        self.MVA_rating = MVA_rating
        
        self.m =m
        self.shift = shift
        self.tap= self.m * np.exp(1j*self.shift)  
        
        self.ts_max_loading = 0
        self.ts_avg_loading = 0
        # Set Cable_type
        self._Cable_type = Cable_type
        
        # If not Custom, update parameters
        if Cable_type != 'Custom':
            self.Cable_type = Cable_type
        else:
            self._calculate_Ybus_branch() 

        self.fromS=0
        self.toS=0
        
        self.loss =0
        
        self.geometry=geometry
        self.direction = 'from'
        
        
        if name in Line_AC.names:
            Line_AC.lineNumber -= 1
            raise NameError("Already used name '%s'." % name)

        if name is None:
            self._name = str(self.lineNumber)
        else:
            self._name = name
            
        self.hover_text = None  
        
        self.isTf = isTf
        
        if self.toNode.kV_base != self.fromNode.kV_base or self.m !=1 or self.shift !=0:
            self.isTf=True
        Line_AC.names.add(self.name)
   
    @property
    def S_base(self):
        return self._S_base
    
    @property
    def life_time_hours(self):
        return self.life_time *8760

    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        if hasattr(self, '_S_base'):  
            old_S_base = self._S_base
            rate = old_S_base / new_S_base
            if self.Ybus_branch is not None and old_S_base != new_S_base:
                self.Ybus_branch /= rate
        self._S_base = new_S_base

    @property
    def Cable_type(self):
        return self._Cable_type
    
    @Cable_type.setter
    def Cable_type(self, new_type):
        self._Cable_type = new_type
        if new_type != 'Custom':
            self.R, self.X, self.G, self.B, self.MVA_rating = self.get_cable_parameters(
                new_type, self.S_base, self.Length_km, self.N_cables,self.kV_base)
            self._calculate_Ybus_branch()  
              
    def _calculate_Ybus_branch(self):
        """
        Calculate the branch admittance matrix (Ybus_branch).
        
        The matrix is structured as:
        [[Yff  Yft]
         [Ytf  Ytt]]
        
        where:
        - Yff: admittance at from-bus to from-bus
        - Yft: admittance at from-bus to to-bus
        - Ytf: admittance at to-bus to from-bus
        - Ytt: admittance at to-bus to to-bus
        """
        self.Z = self.R + self.X * 1j
        self.Y = self.G + self.B * 1j       
        
        branch_ft = -(1/self.Z)/np.conj(self.tap)
        branch_tf = -(1/self.Z)/self.tap
        branch_ff=(1/self.Z+self.Y/2)/(self.m**2)
        branch_tt=(1/self.Z+self.Y/2)
        
        self.Ybus_branch=np.array([[branch_ff, branch_ft],[branch_tf, branch_tt]])
        
class Exp_Line_AC(Line_AC):
    @property
    def capacity_MVA(self):
        return self.MVA_rating * self.np_line

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.kV_base = self.fromNode.kV_base
        self.direction = 'from'
        self.base_cost = 0
        self.life_time = 50
        self.exp_inv=1
        self.cost_perMVAkm = None
        self.phi=0
        
        self.np_line=0  #Actual number of lines

        self.np_line_b=0  #N_b base attribute
        self.np_line_i= 0 #N_i initial guess
        self.np_line_max = 1 #N_max max number of lines
        self.np_line_opf=True
        self.investment_decisions = {
            'planned_installation': [0],
            'planned_decomision': [0],
            'max_inv': [self.np_line_max],
            'np_dynamic': [self.np_line]
        }
        self.hover_text = None

        self.ts_max_loading = 0
        self.ts_avg_loading = 0
        
        self.toNode.connected_toExpLine.append(self)
        self.fromNode.connected_fromExpLine.append(self)

class rec_Line_AC(Line_AC):
    
    @property
    def capacity_MVA(self):
        return self.MVA_rating_new if getattr(self, 'rec_branch', False) else self.MVA_rating

    def __init__(self,r_new,x_new,g_new,b_new,MVA_rating_new,Life_time,base_cost, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.kV_base = self.fromNode.kV_base
        self.direction = 'from'
        self.base_cost = base_cost
        self.life_time = Life_time
        self.exp_inv=1
        self.cost_perMVAkm = None
        self.phi=0

        self.rec_branch = False
        self.rec_line_opf=True

        self.R_new = r_new
        self.X_new = x_new
        self.G_new = g_new
        self.B_new = b_new
        self.MVA_rating_new = MVA_rating_new

        self.ts_max_loading = 0
        self.ts_avg_loading = 0

        # Calculate new Ybus_branch
        self._calculate_Ybus_branch_new()

        self.hover_text = None
        
        self.toNode.connected_toRepLine.append(self)
        self.fromNode.connected_fromRepLine.append(self)
        
    def _calculate_Ybus_branch_new(self):
        """
        Calculate the new branch admittance matrix (Ybus_branch_new) using the new parameters.
        
        The matrix is structured as:
        [[Yff  Yft]
         [Ytf  Ytt]]
        
        where:
        - Yff: admittance at from-bus to from-bus
        - Yft: admittance at from-bus to to-bus
        - Ytf: admittance at to-bus to from-bus
        - Ytt: admittance at to-bus to to-bus
        """
        # Calculate new impedance and admittance
        self.Z_new = self.R_new + self.X_new * 1j
        self.Y_new = self.G_new + self.B_new * 1j       
        
        # Calculate new branch elements
        branch_ft_new = -(1/self.Z_new)/np.conj(self.tap)
        branch_tf_new = -(1/self.Z_new)/self.tap
        branch_ff_new = (1/self.Z_new + self.Y_new/2)/(self.m**2)
        branch_tt_new = (1/self.Z_new + self.Y_new/2)
        
        # Create new Ybus_branch matrix
        self.Ybus_branch_new = np.array([[branch_ff_new, branch_ft_new],
                                        [branch_tf_new, branch_tt_new]])


class Size_selection(Line_AC):
    lineNumber = 0
    names = set()

    @classmethod
    def reset_class(cls):
        cls.lineNumber = 0
        cls.names = set()
        
    @property
    def name(self):
        return self._name

    @property
    def cable_types(self):
        return self._cable_types

    @property
    def life_time_hours(self):
        return self.life_time *8760
    
    @property
    def capacity_MVA(self):
        if self._active_config == -1:
            return 0
        return self.MVA_rating_list[self._active_config]
    
    @property
    def installation_cost(self):
        return self.installation_cost_per_km * self.trench_lenght_km
    
    @cable_types.setter
    def cable_types(self, value):
        """Set cable types and recalculate parameters if the list changes."""
        if value != self._cable_types:
            self._cable_types = value
            # Ensure database is loaded before validation
            if Line_AC._cable_database is None:
                Line_AC.load_cable_database()
            # Validate all cable types exist in database
            for cable_type in self._cable_types:
                if cable_type not in self._cable_database.index:
                    raise ValueError(f"Cable type '{cable_type}' not found in database")
            # Recalculate parameters for all configurations
            self._calculate_all_parameters()
            # Update active parameters
            self._update_active_parameters()

    def __init__(self, fromNode: Node_AC, toNode: Node_AC, cable_types: list = None, active_config: int = 0, Length_km:float=1.0, S_base:float=100, name=None,geometry=None):       
        # Initialize basic line parameters
        self.lineNumber = Size_selection.lineNumber
        Size_selection.lineNumber += 1
        
        self.Length_km = Length_km
        self.S_base = S_base
        self.fromNode = fromNode
        self.toNode = toNode
        self.kV_base = fromNode.kV_base
        self.m = 1
        self.shift = 0
        self.tap= self.m * np.exp(1j*self.shift)  
        
        # Initialize cable-related attributes
        self._cable_types = cable_types if cable_types is not None else []
        self.ini_active_config = active_config
        self._active_config = active_config
        self.direction = 'from'
        # Initialize parameter lists
        self.R_list = []
        self.X_list = []
        self.G_list = []
        self.B_list = []
        self.MVA_rating_list = []
        self.base_cost = []
        self.Ybus_list = []

        self.life_time = 25

        self.ts_max_loading = 0
        self.ts_avg_loading = 0

        self.geometry = geometry
        self.fromS = 0
        self.toS = 0
        self.loss = 0
        self.P_loss =0
        self.network_flow = None    

        self.installation_cost_per_km = 1
        self.trench_lenght_km = self.Length_km

        
        # If cable types are provided, validate and calculate parameters
        if self._cable_types:
            # Ensure database is loaded before validation
            if Line_AC._cable_database is None:
                Line_AC.load_cable_database()
            # Validate all cable types exist in database
            for cable_type in self._cable_types:
                if cable_type not in self._cable_database.index:
                    raise ValueError(f"Cable type '{cable_type}' not found in database")
            
            # Calculate parameters for all configurations
            self._calculate_all_parameters()
        else:
            # No cable types provided - set default zero parameters
            self._set_zero_parameters()
            
        # Add array-specific attributes
        self.array_opf = True  # Flag for optimization

        if name is None:
            self._name = str(self.lineNumber)
        else:
            self._name = name

        # Connect to nodes
        self.toNode.connected_toCTLine.append(self)
        self.fromNode.connected_fromCTLine.append(self)
        
    @property
    def active_config(self):
        return self._active_config
    
    @active_config.setter
    def active_config(self, value):
        if not -1 <= value < len(self._cable_types):
            raise ValueError(f"Configuration index must be between -1 and {len(self._cable_types)-1}")
        self._active_config = value
        self._update_active_parameters()
        
    def _update_active_parameters(self):
        """Update the line parameters based on the active configuration."""
        if self._active_config == -1 or not self._cable_types:
            # No cable selected or no cable types available
            self._set_zero_parameters()
        else:
            if self._active_config >= len(self.R_list):
                self._active_config = len(self.R_list) - 1
            self.R = self.R_list[self._active_config]
            self.X = self.X_list[self._active_config]
            self.G = self.G_list[self._active_config]
            self.B = self.B_list[self._active_config]
            self.Z = self.R + self.X * 1j
            self.Y = self.G + self.B * 1j
            self.MVA_rating = self.MVA_rating_list[self._active_config]
            self.Ybus_branch = self.Ybus_list[self._active_config]  # Use stored matrix
            self.max_active_config = self.MVA_rating_list.index(max(self.MVA_rating_list))
        
    def _set_zero_parameters(self):
        """Set all parameters to zero (no cable selected)."""
        self.R = 0
        self.X = 0
        self.G = 0
        self.B = 0
        self.Z = 0 + 0j
        self.Y = 0 + 0j
        self.MVA_rating = 0
        self.Ybus_branch = np.zeros((2, 2), dtype=complex)  # Zero Ybus matrix
        
    def _calculate_all_parameters(self):
        """Calculate and store parameters for all configurations."""
        # Initialize parameter lists
        self.R_list = []
        self.X_list = []
        self.G_list = []
        self.B_list = []
        self.MVA_rating_list = []
        self.base_cost = []
        self.Ybus_list = []
       
        for cable_type in self._cable_types:
            R, X, G, B, MVA_rating = self.get_cable_parameters(
                cable_type,
                self.S_base,
                self.Length_km,
                1, # Number of parallel lines set default to 1
                self.kV_base
            )
            
            self.R_list.append(R)
            self.X_list.append(X)
            self.G_list.append(G)
            self.B_list.append(B)
            self.MVA_rating_list.append(MVA_rating)
            
            cost_per_km = self.get_cost_parameter(cable_type)
            self.base_cost.append(cost_per_km * self.Length_km)

            Ybus_branch = self.local_Ybus_branch(R,X,G,B)
            self.Ybus_list.append(Ybus_branch)
            
        # Set initial parameters
        self._update_active_parameters()

    def local_Ybus_branch(self,R,X,G,B):
        """
        Calculate the branch admittance matrix (Ybus_branch).
        
        The matrix is structured as:
        [[Yff  Yft]
         [Ytf  Ytt]]
        
        where:
        - Yff: admittance at from-bus to from-bus
        - Yft: admittance at from-bus to to-bus
        - Ytf: admittance at to-bus to from-bus
        - Ytt: admittance at to-bus to to-bus
        """
        Z = R + X * 1j
        Y = G + B * 1j       
        
        branch_ft = -(1/Z)/np.conj(self.tap)
        branch_tf = -(1/Z)/self.tap
        branch_ff=(1/Z+Y/2)/(self.m**2)
        branch_tt=(1/Z+Y/2)
        
        Ybus_branch=np.array([[branch_ff, branch_ft],[branch_tf, branch_tt]])    
        return Ybus_branch

    def add_cable_type(self, cable_type):
        """Add a new cable type to the array."""
        # Ensure database is loaded
        if Line_AC._cable_database is None:
            Line_AC.load_cable_database()
        if cable_type not in self._cable_database.index:
            raise ValueError(f"Cable type '{cable_type}' not found in database")
        self._cable_types.append(cable_type)
        self._calculate_all_parameters()
        
    def remove_cable_type(self, config_index):
        """Remove a cable type from the array."""
        if len(self._cable_types) <= 1:
            raise ValueError("Cannot remove the last cable type")
        if not 0 <= config_index < len(self._cable_types):
            raise ValueError(f"Configuration index must be between 0 and {len(self._cable_types)-1}")
            
        self._cable_types.pop(config_index)
        if self._active_config >= len(self._cable_types):
            self._active_config = len(self._cable_types) - 1
        self._calculate_all_parameters()

    def get_cost_parameter(self,cable_type):
        # Ensure database is loaded
        if Line_AC._cable_database is None:
            Line_AC.load_cable_database()
        return self._cable_database.loc[cable_type, 'Cost_per_km'] if 'Cost_per_km' in self._cable_database.columns else 1
    
    def set_no_cable(self):
        """Set the line to have no cable selected (zero Ybus matrix)."""
        self._active_config = -1
        self._update_active_parameters()
    
    def has_cable_selected(self):
        """Check if a cable is currently selected."""
        return self._active_config >= 0 and self._cable_types

class Cable_options:
    Cable_options_num = 0
    names = set()
    _cable_database = None  
    
    def _calculate_MVA_ratings(self,cable_types):
        mva_ratings = []
        for cable_type in cable_types:
            # Get MVA rating directly from database
            if cable_type in self._cable_database.index:
                cable_data = self._cable_database.loc[cable_type]
                # Calculate MVA rating: A_rating * kV_base * sqrt(3) / 1000
                A_rating = cable_data['A_rating']
                kV_base = cable_data['Nominal_voltage_kV'] 
                MVA_rating = A_rating * kV_base * np.sqrt(3) / 1000
                mva_ratings.append(MVA_rating)
            else:
                raise ValueError(f"Cable type '{cable_type}' not found in database")
        return mva_ratings

    
    def sort_cable_types_by_capacity(self):
        """Sort cable types by MVA rating (smallest to largest)"""
        # Create list of tuples (cable_type, mva_rating)
        cable_ratings = list(zip(self._cable_types, self.MVA_ratings))
        
        # Sort by MVA rating (ascending order)
        cable_ratings.sort(key=lambda x: x[1])
        
        # Update cable types and ratings
        self._cable_types = [cable for cable, _ in cable_ratings]
        self.MVA_ratings = [rating for _, rating in cable_ratings]
        
        # Update all linked lines
        for line in self.lines:
            line.cable_types = self._cable_types

    @classmethod
    def load_cable_database(cls, cable_database=None):
        """Load cable database from YAML files if not already loaded, or use provided DataFrame.
        
        Parameters
        ----------
        cable_database : pd.DataFrame, optional
            If provided, use this DataFrame as the cable database instead of loading from YAML files.
            The DataFrame should have cable names as index and cable specifications as columns.
        """
        if cls._cable_database is None:
            if cable_database is not None:
                # Use provided DataFrame
                cls._cable_database = cable_database.copy()
            else:
                # Load from YAML files
                # Get the path to the Cable_database directory
                module_dir = Path(__file__).parent
                cable_dir = module_dir / 'Cable_database'
                
                data_dict = {}
                # Read all YAML files in the directory
                for yaml_file in cable_dir.glob('*.yaml'):
                    with open(yaml_file, 'r', encoding='latin-1') as f:
                        cable_data = yaml.safe_load(f)
                        if cable_data:
                            # Each file has one cable
                            cable_name = list(cable_data.keys())[0]
                            specs = cable_data[cable_name]
                            
                            # Only include AC cables
                            if specs.get('Type', 'AC') == 'AC':
                                data_dict[cable_name] = specs
                
                if data_dict:
                    # Convert to pandas DataFrame
                    cls._cable_database = pd.DataFrame.from_dict(data_dict, orient='index')
    
    def __init__(self, cable_types: list = None, name=None, cable_database=None):
        self.Cable_options_num = Cable_options.Cable_options_num
        Cable_options.Cable_options_num += 1
        
        # Load database if not already loaded, or use provided database
        if Cable_options._cable_database is None:
            Cable_options.load_cable_database(cable_database=cable_database)
        elif cable_database is not None:
            # Override existing database with provided one
            Cable_options._cable_database = cable_database.copy()
        
        # If cable_types is None or empty, create empty cable option
        if cable_types is None or len(cable_types) == 0:
            self._cable_types = []
            self.MVA_ratings = []
        else:
            self._cable_types = cable_types
            self.lines = []
            self.active_config = None
            # Efficiently calculate MVA ratings in one pass
            self.MVA_ratings = self._calculate_MVA_ratings(self._cable_types)
            
            # Sort by capacity (smallest to largest)
            self.sort_cable_types_by_capacity()
        
        if name is None:
            self.name = str(self.Cable_options_num)
        else:
            self.name = name
            
        Cable_options.names.add(self.name)
        
    @property
    def cable_types(self):
        return self._cable_types
    
    @cable_types.setter
    def cable_types(self, new_cable_types):
        """Set cable types and update all linked lines"""
        self._cable_types = new_cable_types
        
        # Recalculate MVA ratings
        self.MVA_ratings = self._calculate_MVA_ratings(self._cable_types)

        
        # Update all linked lines
        for line in self.lines:
            line.cable_types = self._cable_types

class TF_Line_AC:
    trafNumber = 0
    names = set()

    @classmethod
    def reset_class(cls):
        cls.trafNumber = 0
        cls.names = set()
        
    @property
    def name(self):
        return self._name

    def __init__(self, fromNode: Node_AC, toNode: Node_AC,  r: float, x: float, g: float, b: float, MVA_rating: float, kV_base: float,m:float=1, shift:float=0, name=None):
        self.trafNumber = TF_Line_AC.trafNumber
        TF_Line_AC.trafNumber += 1

        self.fromNode = fromNode
        self.toNode = toNode
        self.direction = 'from'
        self.R = r
        self.X = x
        self.G = g
        self.B = b
        self.Z = self.R + self.X * 1j
        self.Y = self.G + self.B * 1j
        self.kV_base = kV_base
        self.MVA_rating = MVA_rating

        self.ts_max_loading = 0
        self.ts_avg_loading = 0

        self.m =m
        self.shift = shift
        
        tap= self.m * np.exp(1j*self.shift)            
        #Yft
        branch_ft = -(1/self.Z)/np.conj(tap)
        
        #Ytf
        branch_tf = -(1/self.Z)/tap
        
        branch_ff=(1/self.Z+self.Y/2)/(self.m**2)
        branch_tt=(1/self.Z+self.Y/2)
        
        self.Ybus_branch=np.array([[branch_ff, branch_ft],[branch_tf, branch_tt]])
        
        self.fromS=0
        self.toS=0
        
        self.toNode.connected_toTFLine.append(self)
        self.fromNode.connected_fromTFLine.append(self)

        self.hover_text = None
        self.isTf = True
        if name in TF_Line_AC.names:
            TF_Line_AC.trafNumber -= 1
            raise NameError("Already used name '%s'." % name)

        if name is None:
            self._name = str(self.lineNumber)
        else:
            self._name = name
            
        TF_Line_AC.names.add(self.name)
        

class Line_DC:
    """
    Attributes
    ----------
    fromNode : Node_DC
        The starting node of the line
    toNode : Node_DC
        The ending node of the line
    r : float
        Resistance of the line in pu    
    MW_rating : float
        MVA rating of the line
    km : float
        Length of the line in km
    polarity : str
        Polarity of the line ('m' or 'b' or 'sm')   
    N_cables : int
        Number of cables in the line
    Cable_type : str
        Type of cable in the line
    S_base : float
        Base power of the line in MVA
    """
    lineNumber = 0
    names = set()
    _cable_database = None

    
    @classmethod
    def load_cable_database(cls, cable_database=None):
        """Load cable database from YAML files if not already loaded, or use provided DataFrame.
        
        Parameters
        ----------
        cable_database : pd.DataFrame, optional
            If provided, use this DataFrame as the cable database instead of loading from YAML files.
            The DataFrame should have cable names as index and cable specifications as columns.
            Only DC cables will be used (filtered by Type='DC' if Type column exists).
        """
        if cls._cable_database is None:
            if cable_database is not None:
                # Use provided DataFrame, but filter for DC cables if Type column exists
                if 'Type' in cable_database.columns:
                    type_norm = cable_database['Type'].astype(str).str.upper().replace({'HVAC': 'AC', 'HVDC': 'DC'})
                    cls._cable_database = cable_database[type_norm == 'DC'].copy()
                else:
                    # Assume all are DC if no Type column
                    cls._cable_database = cable_database.copy()
            else:
                # Load from YAML files
                # Get the path to the Cable_database directory
                module_dir = Path(__file__).parent
                cable_dir = module_dir / 'Cable_database'
                
                data_dict = {}
                # Read all YAML files in the directory
                for yaml_file in cable_dir.glob('*.yaml'):
                    with open(yaml_file, 'r', encoding='latin-1') as f:
                        cable_data = yaml.safe_load(f)
                        if cable_data:
                            # Each file has one cable
                            cable_name = list(cable_data.keys())[0]
                            specs = cable_data[cable_name]
                            
                            # Only include DC cables
                            typ = str(specs.get('Type', 'DC')).upper()
                            if typ in ('HVDC', 'DC'):
                                data_dict[cable_name] = specs
                
                if data_dict:
                    # Convert to pandas DataFrame
                    cls._cable_database = pd.DataFrame.from_dict(data_dict, orient='index')
                    #print(f"Loaded {len(data_dict)} DC cables into database")
                else:
                    print("No DC cable data found in any YAML files")

    @classmethod
    def reset_class(cls):
        cls.lineNumber = 0
        cls.names = set()    
   
    @property
    def life_time_hours(self):
        return self.life_time *8760     
        
    @property
    def name(self):
        return self._name
    @property
    def power_MW(self):
        return max(abs(self.fromP), abs(self.toP)) * self.S_base

    @property
    def capacity_MW(self):
        return self.MW_rating * self.np_line

    @property
    def loading(self):
        cap = self.capacity_MW
        return 0.0 if cap == 0 else (self.power_MW / cap) * 100.0

    def get_cable_parameters(self, Cable_type, S_base, Length_km, N_cables,kV_base):
        from .grid_analysis import Cable_parameters
        """Get cable parameters from the database."""
        # Ensure database is loaded
        if Line_DC._cable_database is None:
            Line_DC.load_cable_database()
        Cable_type = Cable_type.replace(' ', '_')
        if Cable_type not in self._cable_database.index:
            raise ValueError(f"Cable type '{Cable_type}' not found in database")
        
        # Get cable data
        cable_data = self._cable_database.loc[Cable_type]
        
        # Calculate parameters
        R_Ohm = cable_data['R_Ohm_km'] 
        L_mH = 0
        C_uF = 0
        G_uS = 0
        A_rating = cable_data['A_rating']
        km = Length_km

        r, _, _, _, MW_rating = Cable_parameters(S_base, R_Ohm, L_mH, C_uF, G_uS, A_rating, kV_base, km,1)
        return r, MW_rating
    
    def __init__(self, fromNode: Node_DC, toNode: Node_DC, r: float=0.001, MW_rating: float=9999,km:float=1, polarity='m', name=None,N_cables=1,Cable_type:str='Custom',S_base:float=100):
        self.lineNumber = Line_DC.lineNumber
        Line_DC.lineNumber += 1

        self.m_sm_b = polarity
        self.S_base = S_base
        if polarity == 'm':
            self.pol = 1
        elif polarity == 'b' or polarity == 'sm':
            self.pol = 2
        else:
            print('No viable polarity inserted pol =1')
            self.pol = 1

        self.fromNode = fromNode
        self.toNode = toNode
        self.kV_base = toNode.kV_base

        self.np_line=N_cables

        self.np_line_b=N_cables
        self.np_line_i= N_cables
        self.np_line_max = N_cables
        self.np_line_opf=False
        self.investment_decisions = {
            'planned_installation': [0],
            'planned_decomision': [0],
            'max_inv': [self.np_line_max],
            'np_dynamic': [self.np_line]
        }

        self.R = r
        self.MW_rating = MW_rating
        self.Length_km=km

        self._Cable_type = Cable_type

        if Cable_type != 'Custom':
            self.Cable_type=Cable_type
        

        self.fromP=0
        self.toP=0        
        self.direction = 'from'
 
        self.loss =0

        self.ts_max_loading = 0
        self.ts_avg_loading = 0
        
        self.base_cost = 0
        self.life_time = 50
        self.exp_inv=1
        self.cost_perMWkm = None
        self.phi=1
               
         
        self.hover_text = None
        self.geometry=None
        if name in Line_DC.names:
            Line_DC.lineNumber -= 1
            raise NameError("Already used name '%s'." % name)

        if name is None:
            self._name = str(self.lineNumber)
        else:
            self._name = name

        Line_DC.names.add(self.name)

    @property
    def S_base(self):
        return self._S_base
    
    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        if hasattr(self, '_S_base'):  
            old_S_base = self._S_base
            rate = old_S_base / new_S_base
            if self.R is not None and old_S_base != new_S_base:
                self.R *= rate
        self._S_base = new_S_base        
    @property
    def Cable_type(self):
        return self._Cable_type
    
    @Cable_type.setter
    def Cable_type(self, new_type):
        self._Cable_type = new_type
        if new_type != 'Custom':
            self.R, self.MW_rating = self.get_cable_parameters(new_type, self.S_base, self.Length_km, self.np_line,self.kV_base)

class CFC_DC:
    CFC_num = 0
    names = set()

    @classmethod
    def reset_class(cls):
        cls.CFC_num = 0
        cls.names = set()

class AC_DC_converter:
    """
    Attributes
    ----------
    AC_type : str
        Type of AC node ('Slack' or 'PV' or 'PQ')
    DC_type : str
        Type of DC node ('Slack' or 'P' or 'Droop' or 'PAC')           
    AC_node : Node_AC
        AC node connected to the converter
    DC_node : Node_DC
        DC node connected to the converter
    P_AC : float
        Active power injection in AC node in pu
    Q_AC : float
        Reactive power injection in AC node in pu
    P_DC : float
        Active power injection in DC node in pu
    Transformer_resistance : float
        Transformer resistance in pu
    Transformer_reactance : float
        Transformer reactance in pu
    Phase_Reactor_R : float
        Phase reactor resistance in pu
    Phase_Reactor_X : float
        Phase reactor reactance in pu
    Filter : float
        Filter in pu
    Droop : float
        Droop in pu
    kV_base : float
        Base voltage in kV
    MVA_max : float
        Maximum MVA rating of the converter
    nConvP : float
        Number of parallel converters
    polarity : int
        Polarity of the converter (1 or -1)
    lossa : float
        No load loss factor for active power
    lossb : float
        Linear currentr loss factor 
    losscrect : float
        Switching loss factor for rectifier
    losscinv : float
        Switching loss factor for inverter
    Ucmin : float
        Minimum voltage magnitude in pu
    Ucmax : float
        Maximum voltage magnitude in pu
    name : str
        Name of the converter
    """
    
    ConvNumber = 0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.ConvNumber = 0
        cls.names = set()
    
    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value
        self.Node_DC.type = value  # Update DC_node type when converter type changes

    @property
    def np_conv(self):
        return self._np_conv

    @np_conv.setter
    def np_conv(self, value):
        self._np_conv = value
        self.Node_DC.Nconv= value
        P_DC = self.P_DC
        P_s = self.P_AC 
        Q_s = self.Q_AC 
        S = np.sqrt(P_s**2 + Q_s**2)
        self.Node_DC.conv_loading = max(S, abs(P_DC)) 
        
    @property
    def life_time_hours(self):
        return self.life_time *8760  

    @property
    def capacity_MVA(self):
        # Treat non-positive as 0; np_conv may be 0 before sizing
        return max(self.MVA_max * getattr(self, 'np_conv', 1), 0.0)

    @property
    def loading(self):
        cap = self.capacity_MVA
        return 0.0 if cap == 0 else (self.apparent_MVA / cap) * 100.0

    @property
    def apparent_MVA(self):
        return max(abs(getattr(self, 'P_AC', 0.0)), abs(getattr(self, 'P_DC', 0.0))) * self.S_base
    
    @property
    def S_base(self):
        return self._S_base
    
    @S_base.setter
    def S_base(self, new_S_base):
        if new_S_base <= 0:
            raise ValueError("S_base must be positive")
        if hasattr(self, '_S_base'):  
            old_S_base = self._S_base
            rate = old_S_base / new_S_base
            if self.R is not None and old_S_base != new_S_base:
                self.R_t *= rate
                self.X_t *= rate
                self.PR_R *= rate
                self.PR_X *= rate
                self.Bf *= rate
                self.P_DC *= rate
                self.P_AC *= rate
                self.Q_AC *= rate
                self.Z_Y_parameters()
    
        self._S_base = new_S_base     

    
    def Z_Y_parameters(self):
            self.Ztf = self.R_t+1j*self.X_t
            self.Zc = self.PR_R+1j*self.PR_X
            if self.Bf != 0:
                self.Zf = 1/(1j*self.Bf)
            else:
                self.Zf = 0

            if self.R_t != 0:
                self.Y_tf = 1/self.Ztf
                self.Gtf = np.real(self.Y_tf)
                self.Btf = np.imag(self.Y_tf)
            else:
                self.Gtf = 0
                self.Btf = 0

            if self.PR_R != 0:
                self.Y_c = 1/self.Zc
                self.Gc = np.real(self.Y_c)
                self.Bc = np.imag(self.Y_c)
            else:
                self.Gc = 0
                self.Bc = 0
                
            self.Z1 = 0
            self.Z2 = 0
            self.Z3 = 0
            if self.Zf != 0:
                self.Z2 = (self.Ztf*self.Zc+self.Zc*self.Zf+self.Zf*self.Ztf)/self.Zf
            if self.Zc != 0:
                self.Z1 = (self.Ztf*self.Zc+self.Zc*self.Zf+self.Zf*self.Ztf)/self.Zc
            if self.Ztf != 0:
                self.Z3 = (self.Ztf*self.Zc+self.Zc*self.Zf+self.Zf*self.Ztf)/self.Ztf


        

    def __init__(self, AC_type: str, DC_type: str, AC_node: Node_AC, DC_node: Node_DC,P_AC: float=0, Q_AC: float=0, P_DC: float=0, Transformer_resistance: float=0, Transformer_reactance: float=0, 
            Phase_Reactor_R: float=0, Phase_Reactor_X: float=0, Filter: float=0, Droop: float=0, kV_base: float=345, MVA_max: float = 1.05,nConvP: float =1,polarity: int =1 ,
            lossa:float=1.103,lossb:float= 0.887,losscrect:float=2.885,losscinv:float=4.371,Ucmin: float = 0.85, Ucmax: float = 1.2,arm_res:float=0.001, S_base:float=100, name=None):
        self.ConvNumber = AC_DC_converter.ConvNumber
        AC_DC_converter.ConvNumber += 1
        # type: (1=P, 2=droop, 3=Slack)
        self.S_base = S_base
        self._np_conv= nConvP

        self.np_conv_b= nConvP
        self.np_conv_i= nConvP
        self.np_conv_max = nConvP
        
        self.np_conv_opf=False
        self.investment_decisions = {
            'planned_installation': [0],
            'planned_decomision': [0],
            'max_inv': [self.np_conv_max],
            'np_dynamic': [self.np_conv]
        }
        self.base_cost = 0
        self.life_time = 50
        self.exp_inv=1
        self.cost_perMVA = None
        self.phi=1
 
        self.cn_pol=   polarity 
        
        self.Droop_rate = Droop
        
        self.AC_type = AC_type

        self.AC_kV_base = kV_base
        self.DC_kV_base = DC_node.kV_base

        self.Node_AC = AC_node
        
        AC_node.Num_conv_connected+=1
        
        self.Node_DC = DC_node
        self.Node_DC.Nconv= nConvP
        self.Node_DC.Nconv_i= nConvP
        self.Node_DC.ConvInv =True
        self.Node_DC.conv_MW=MVA_max* self.cn_pol
        # if self.AC_type=='Slack':
        #     # print(name)mm
        #     self.type='PAC'

        self.ts_max_loading = 0
        self.ts_avg_loading = 0


        self.type = DC_type

        self.R_t = Transformer_resistance/self.cn_pol
        self.X_t = Transformer_reactance /self.cn_pol
        self.PR_R = Phase_Reactor_R /self.cn_pol
        self.PR_X = Phase_Reactor_X /self.cn_pol
        self.Bf = Filter * self.cn_pol
        self.P_DC = P_DC
        self.P_AC = P_AC
        self.Q_AC = Q_AC
        
        # self.Node_DC.type = DC_type
        self.Node_DC.Droop_rate = self.Droop_rate
        self.Node_DC.Pconv = self.P_DC
        
         
        self.a_conv_og  = lossa  * self.cn_pol # MVA
        self.b_conv_og  = lossb                  # kV
        self.c_rect_og  = losscrect  /self.cn_pol  # Ohm
        self.c_inver_og = losscinv /self.cn_pol  # Ohm

        # 1.103 0.887  2.885    4.371
        

        self.ra_og = arm_res
        self.ra = arm_res *self.cn_pol  # Ohm
       
        self.power_loss_model = 'quadratic'
        self.Vsum = 0
        
        
        self.P_loss = 0
        self.P_loss_tf = 0

        self.U_s = 1
        if P_DC > 0:
            self.U_c = 0.98
            self.U_f = 0.99
        else:
            self.U_c = 1.1
            self.U_f = 1.05
        self.th_s = 0.09
        self.th_f = 0.1
        self.th_c = 0.11

        self.MVA_max = MVA_max * self.cn_pol
        self.Ucmin = Ucmin
        self.Ucmax = Ucmax
        self.OPF_fx=False
        self.OPF_fx_type='PDC'
        
        if self.AC_type=='Slack':
            self.OPF_fx_type='None'
            
        if self.AC_type == 'PV':
            if self.type == 'PAC':
                self.OPF_fx_type='PV'
            elif self.type == 'Slack':
                self.OPF_fx_type='None'
            if self.Node_AC.type == 'PQ':
                self.Node_AC.type = 'PV'
        if self.AC_type == 'PQ':
            if  self.type == 'PAC':
                self.OPF_fx_type='PQ'
            else:
                self.OPF_fx_type='Q'
            self.Node_AC.Q_s_fx += self.Q_AC
           

        self.Qc = 0
        self.Pc = 0

        self.Z_Y_parameters()

        self.hover_text = None
        self.geometry = None

        if name in AC_DC_converter.names:
            AC_DC_converter.ConvNumber -= 1
            raise NameError("Already used name '%s'." % name)

        if name is None:
            self._name = str(self.ConvNumber)
        else:
            self._name = name

        AC_DC_converter.names.add(self.name)
        self.Node_AC.connected_conv.add(self.ConvNumber)

     

class DCDC_converter:
    ConvNumber = 0
    names = set()

    @classmethod
    def reset_class(cls):
        cls.ConvNumber = 0
        cls.names = set()

    
    @property
    def name(self):
        return self._name

    def __init__(self, fromNode: Node_DC, toNode: Node_DC, Pset: float, r: float, MW_rating: float, name=None,geometry=None):
        self.ConvNumber = DCDC_converter.ConvNumber
        DCDC_converter.ConvNumber += 1
        # type: (1=P, 2=droop, 3=Slack)
        # self.type = element_type

        self.ts_max_loading = 0
        self.ts_avg_loading = 0

        self.fromNode = fromNode
        self.toNode = toNode
        self.Pset = Pset
        self.r = r
        self.MW_rating = MW_rating
        self.Powerto = Pset
        self.Powerfrom = -( Pset+Pset**2*r) #Current assumed at VDC = 1 pu
        self.loss = Pset**2*r               #Current assumed at VDC = 1 pu
        fromNode.PconvDC += self.Powerfrom
        fromNode.connected_DCDC_from.add(self.ConvNumber)
        toNode.PconvDC += self.Powerto
        toNode.connected_DCDC_to.add(self.ConvNumber)
        
        if name is None:
            self._name = str(self.ConvNumber)
        else:
            self._name = name

        DCDC_converter.names.add(self.name)

class Ren_source_zone:
    ren_source_num = 0
    names  = set()
    @classmethod
    def reset_class(cls):
        cls.ren_source_num = 0
        cls.names = set()
    
    @property
    def name(self):
        return self._name
    
    @property
    def PRGi_available(self):
        return self._PRGi_available

    @PRGi_available.setter
    def PRGi_available(self, value):
        self._PRGi_available = value
        for ren_source in self.RenSources:
                ren_source.PRGi_available=value
                ren_source.Ren_source_zone = self.name

    @property
    def np_rsgen(self):
        return self.np_rsgen
    
    @np_rsgen.setter
    def np_rsgen(self, value):
        self.np_rsgen = value
        for ren_source in self.RenSources:
            ren_source.np_rsgen=value


    def __init__(self,name=None):
           self.ren_source_num = Ren_source_zone.ren_source_num
           Ren_source_zone.ren_source_num += 1
           
           self.RenSources=[]
           self._PRGi_available=1
           self._np_rsgen=1
           
           self.TS_dict = {
               'PRGi_available': None
           }

           self.inv_dict = {
               'np_rsgen': None
           }
           
           if name is None:
               self._name = str(self.ren_source_num)
           else:
               self._name = name

class Price_Zone:
    price_zone_num = 0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.price_zone_num = 0
        cls.names = set()
    
    @property
    def name(self):
        return self._name
    
    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = value
        for node in self.nodes_AC:
            node.price=value
            for gen in node.connected_gen:
                if gen.price_zone_link:
                    gen.lf=value
                    gen.qf=0
        # Notify all linked MTDC price_zones about the price change
        for mtdc_price_zone in self.mtdc_price_zones:
            mtdc_price_zone.update_price()  # Automatically update MTDC price_zone's price
            
        # If this price_zone has a linked price_zone, update the linked price_zone's price
        if self.linked_price_zone is not None:
            self.linked_price_zone.price = value  # This will trigger the price setter of the offshore price_zone
    @property
    def a_base(self):
        return self._a_base
    
    @a_base.setter
    def a_base(self, value):
        self._a_base = value
        self.update_a()

    @property
    def elasticity(self):
        return self._elasticity

    @elasticity.setter
    def elasticity(self, value):
        self._elasticity = value
        self.update_a()

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, value):
        self._b = value
        if self.expand_import:
            self.calc_import_expand()
        else:
            self.calc_elasticity_effect()

    @property
    def PGL_min_base(self):
        return self._PGL_min_base

    @PGL_min_base.setter
    def PGL_min_base(self, value):
        self._PGL_min_base = value
        if self.expand_import:
            self.calc_import_expand()
        else:
            self.calc_elasticity_effect()
        
    def update_a(self):
        if self.expand_import:
            self.calc_import_expand()
        else:
            self.calc_elasticity_effect()
            
    @property
    def import_expand(self):
        return self._import_expand

    @import_expand.setter
    def import_expand(self, value):
        self._import_expand = value
        self.calc_import_expand()
       
    def calc_elasticity_effect(self):
        self.a = self._a_base*self._elasticity
        if self.b >0 and self.a != 0 and self._elasticity != 1:
            self.PGL_min = -self.b/(self.a*2)
        else:
            self.PGL_min = self._PGL_min_base
            
    def calc_import_expand(self):
        if self.b > 0 and self.expand_import:
            self.PGL_min = self.PGL_min_base - self._import_expand
            a = -self.b / (2 * self.PGL_min * self.S_base) 
            self.a = a*self._elasticity
       

    @property
    def PLi_inv_factor(self):
        return self._PLi_inv_factor
    
    @PLi_inv_factor.setter
    def PLi_inv_factor(self, value):
        self._PLi_inv_factor = value
        for node in self.nodes_AC:
            if node.PLi_linked:
                node.PLi_inv_factor=value
        for node in self.nodes_DC:
            if node.PLi_linked:
                node.PLi_inv_factor=value

    @property
    def PLi_factor(self):
        return self._PLi_factor

    @PLi_factor.setter
    def PLi_factor(self, value):
        self._PLi_factor = value
        for node in self.nodes_AC:
            if node.PLi_linked:
                node.PLi_factor=value
        for node in self.nodes_DC:
            if node.PLi_linked:
                node.PLi_factor=value        

    def __init__(self,price=1,import_pu_L=1,export_pu_G=1,a=0,b=1,c=0,import_expand=0,elasticity=1,S_base:float=100,name=None):
        self.price_zone_num = Price_Zone.price_zone_num
        Price_Zone.price_zone_num += 1
        
        self.expand_import = False
        self._import_expand = import_expand
        self._a_base = a
        self._elasticity = elasticity
        
        self.import_pu_L=import_pu_L
        self.export_pu_G=export_pu_G

        self.S_base=S_base

        self.nodes_AC=[]
        self.nodes_DC=[]
        self.ConvACDC=[]
        
        self._price=price
        self.a=a
        self._b=b
        self.c=c
        self.PGL_min_base=-np.inf

        self.PGL_min=self.PGL_min_base
        self.PGL_max=np.inf
        
        self.PN= 0
        
        
        
        
        
        self.TS_dict = {
            'Load' : None,
            'price': None,
            'a_CG': None,
            'b_CG': None,
            'c_CG': None,
            'PGL_min': None,
            'PGL_max': None
        }
        self.investment_decisions = {
            'Load': [],
            'elasticity': [],
            'import_expand': []
        }
        
        self.df= pd.DataFrame(columns=['time','a', 'b', 'c','price','PGL_min','PGL_max'])        
        self.df.set_index('time', inplace=True)
        self.mtdc_price_zones=[]
        
        self._PLi_factor=1
        self._PLi_inv_factor=1
        
        if name is None:
            self._name = str(self.price_zone_num)
        else:
            self._name = name

        Price_Zone.names.add(self.name)
        
        # To hold the linked price_zone
        self.linked_price_zone = None
    
    
    def link_mtdc_price_zone(self, mtdc_price_zone):
        """Register an MTDC price_zone to be notified when this price_zone's price changes."""
        if mtdc_price_zone not in self.mtdc_price_zones:
            self.mtdc_price_zones.append(mtdc_price_zone)
            
    def link_price_zone(self, other_price_zone):
        """Link another price_zone to this price_zone"""
        self.linked_price_zone = other_price_zone
        
        other_price_zone.price = self.price  # Initially synchronize the price

class OffshorePrice_Zone(Price_Zone):
    def __init__(self, main_price_zone, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_price_zone = main_price_zone  # Keep reference to the main price_zone
        
        # Automatically set specific attributes for OffshorePrice_Zone
        self.a = 0
        self.b = 0
        self.PGL_min = 0
        self.PGL_max = np.inf

    @property
    def price(self):
        return self._price
    
    @price.setter
    def price(self, value):
        if value != self.main_price_zone.price:
            return  # Do not change offshore price_zone's price if it doesn't match main price_zone's price
        
        # Set the offshore price_zone price and update the nodes' prices
        self._price = value
        for node in self.nodes_AC:
            node.price = value  # Update prices of nodes in the offshore price_zone

class MTDCPrice_Zone(Price_Zone):
    def __init__(self, linked_price_zones=None, pricing_strategy='avg', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked_price_zones = linked_price_zones or []  # List to store linked price_zones
        self.pricing_strategy = pricing_strategy  # 'min', 'max', or 'avg'
        self.a = 0  # Default specific MTDC properties
        self.b = 0
        self.PGL_min = 0
        self.PGL_max = np.inf
        # Register this MTDC price_zone with the linked price_zones
        for price_zone in self.linked_price_zones:
            price_zone.link_mtdc_price_zone(self)
        
        self.update_price()  # Set initial price based on linked price_zones

    def add_linked_price_zone(self, price_zone):
        """Add a price_zone to the linked price_zones list."""
        if price_zone not in self.linked_price_zones:
            self.linked_price_zones.append(price_zone)
            price_zone.link_mtdc_price_zone(self)
            self.update_price()  # Update price whenever a new price_zone is added

    def update_price(self):
        """Update the price of the MTDC price_zone based on the linked price_zones and strategy."""
        if not self.linked_price_zones:
            return  # No linked price_zones, no price change

        prices = [price_zone.price for price_zone in self.linked_price_zones]
        
        if self.pricing_strategy == 'min':
            self._price = min(prices)
        elif self.pricing_strategy == 'max':
            self._price = max(prices)
        elif self.pricing_strategy == 'avg':
            self._price = sum(prices) / len(prices)

        # Update node prices based on the new MTDC price
        for node in self.nodes_AC:
            node.price = self._price

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        # Price is managed by linked price_zones, so don't allow manual setting
        s=1
    # Allow for manual override if desired
    def override_price(self, value):
        self._price = value
        for node in self.nodes_AC:
            node.price = value
            
            
            
            
class TimeSeries:
    TS_num = 0
    names = set()
    
    @classmethod
    def reset_class(cls):
        cls.TS_num = 0
        cls.names = set()
    
    @property
    def name(self):
        return self._name

    def __init__(self, element_type: str, element_name:str, data: float, name=None):
        self.TS_num = TimeSeries.TS_num
        TimeSeries.TS_num += 1
        
        
        self.type = element_type
        self.element_name=element_name
        self.data = data
        
        s = 1
        if name is None:
            self._name = str(self.TS_AC_num)
        else:
            self._name = name

        TimeSeries.names.add(self.name)
