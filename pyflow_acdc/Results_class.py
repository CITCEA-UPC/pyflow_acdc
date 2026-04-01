import os
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 12:59:08 2024

@author: BernardoCastro
"""
import numpy as np
from prettytable import PrettyTable as pt
import matplotlib.pyplot as plt
import pandas as pd

from .Classes import Price_Zone


class Results:
    def __init__(self, Grid, decimals=2, export_location=None, export_type="csv", save_res=False):
        self.Grid = Grid
        self.dec = decimals
        # Default export folder if none provided
        if export_location is None:
            export_location = "pyflowacdc_res"
        self.export_location = export_location
        # Whether to actually write results to disk
        self.save_res = save_res
        # Ensure export directory exists
        os.makedirs(self.export_location, exist_ok=True)
        # export_type controls how results are written when self.export is not None:
        # "csv"  -> keep current CSV exports
        # "excel" -> single Excel workbook with one sheet per results table
        # any other value -> no automatic file export
        self.export_type = export_type
        # Central registry for all DataFrames produced by this Results instance
        # Keys are method-level names such as "AC_Powerflow", "AC_voltage", etc.
        self.tables = {}

    def options(self):
        # Get all attributes (including methods) of the class
        all_attributes = dir(self)

        # Filter out only the methods (defs)
        methods = [attribute for attribute in all_attributes if callable(
            getattr(self, attribute)) and not attribute.startswith('__')]

        # Print the method names
        for method_name in methods:
            print(method_name)
    # def export(self):

    def All(self, decimals=None, export_location=None, export_type=None,print_table=True, file_name=None,opt_exit=True):
        # Allow overriding configuration for this run
        if decimals is not None:
            self.dec = decimals
        if export_location is not None:
            self.export_location = export_location
            os.makedirs(self.export_location, exist_ok=True)
            self.save_res = True
        if export_type is not None:
            self.export_type = export_type
            self.save_res = True
            if export_location is None:
                self.export_location = "pyflowacdc_res"
                os.makedirs(self.export_location, exist_ok=True)

        # Pull latest prebuilt Pyomo model results table persisted by pyomo_model_solve.
        df_pyomo = getattr(self.Grid, "_last_pyomo_model_results_table", None)
        if isinstance(df_pyomo, pd.DataFrame):
            self.tables["Pyomo_Model_Results"] = df_pyomo.copy()
            if print_table and not df_pyomo.empty:
                print('--------------')
                print('Pyomo Model Results')
                print('')
                table = pt()
                table.field_names = ['Property', 'Value']
                table.align['Property'] = 'l'
                table.align['Value'] = 'r'
                row = df_pyomo.iloc[0].to_dict()
                for key, val in row.items():
                    table.add_row([key, val])
                print(table)
            if opt_exit and not df_pyomo.empty and "Solution Found" in df_pyomo.columns:
                solution_found = bool(df_pyomo["Solution Found"].iloc[0])
                if not solution_found:
                    return
        if self.Grid.Clustering_information != {}:
            self.Clustering_results(print_table=print_table)
        if self.Grid.nodes_AC != []:
            self.AC_Powerflow(print_table=print_table)
            self.AC_voltage(print_table=print_table)
            self.AC_lines_current(print_table=print_table)
            self.AC_lines_power(print_table=print_table)
        
        if self.Grid.nodes_DC != []:
            if self.Grid.nconv != 0:
                self.Converter(print_table=print_table)
            self.DC_bus(print_table=print_table)
            self.DC_lines_current(print_table=print_table)
            self.DC_lines_power(print_table=print_table)
            

            if self.Grid.Converters_DCDC != []:
                self.DC_converter(print_table=print_table)
        
        if self.Grid.nodes_AC != [] and self.Grid.nodes_DC != []:
            self.Slack_All(print_table=print_table)
            
        elif self.Grid.nodes_AC != []:
            self.Slack_AC(print_table=print_table)

        self.Power_loss(print_table=print_table)
        if self.Grid.OPF_run :
            if self.Grid.Generators != [] or self.Grid.Generators_DC != []:
                self.Ext_gen(print_table=print_table)
            if self.Grid.RenSources:
                self.Ext_REN(print_table=print_table)
            if not self.Grid.TEP_run and not self.Grid.MP_TEP_run:
                self.OBJ_res(print_table=print_table)
            if self.Grid.Price_Zones != []: 
                self.Price_Zone(print_table=print_table)    
        if self.Grid.lines_AC_exp+self.Grid.lines_AC_rec+self.Grid.lines_AC_ct != []:
            self.AC_exp_lines_power(print_table=print_table)
        if self.Grid.TEP_run:    
            self.TEP_N(print_table=print_table)
            if self.Grid.TEP_multiScenario_res is not None:
                self.TEP_TS_norm(print_table=print_table)
                self.TEP_multiScenario_res(print_table=print_table)
                s=1
            else:
                self.TEP_norm(print_table=print_table)
        if self.Grid.MP_TEP_run:
            self.MP_TEP_results(print_table=print_table)
            self.MP_TEP_obj_res(print_table=print_table)
            self.MP_TEP_fuel_type_distribution(print_table=print_table)
        if self.Grid.MP_MS_TEP_run:
            self.MP_TEP_results(print_table=print_table)
            self.MP_MS_TEP_results(print_table=print_table)
            self.MP_MS_TEP_obj_res(print_table=print_table)
            self.MP_TEP_fuel_type_distribution(print_table=print_table)
        if getattr(self.Grid, "Seq_STEP_run", False):
            self.Seq_STEP_results(print_table=print_table)
            self.Seq_STEP_obj_res(print_table=print_table)
            self.Seq_STEP_fuel_type_distribution(print_table=print_table)
        if getattr(self.Grid, "Seq_MS_STEP_run", False):
            self.Seq_MS_STEP_results(print_table=print_table)
            self.Seq_MS_STEP_obj_res(print_table=print_table)
            self.Seq_MS_STEP_fuel_type_distribution(print_table=print_table)
        # Final separator for All() run
        print('------')

        # Optional Excel export of all collected tables
        if self.save_res and self.export_type == "excel" and self.tables:
            base_name = file_name if file_name else (getattr(self.Grid, "name", None) or "pyflowacdc")
            excel_path = os.path.join(self.export_location, f"{base_name}_results.xlsx")
            with pd.ExcelWriter(excel_path) as writer:
                for name, df in self.tables.items():
                    if not isinstance(df, pd.DataFrame):
                        continue
                    # Excel sheet names max length 31
                    sheet_name = name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

    def All_AC(self, print_table=True):
        self.AC_Powerflow(print_table=print_table)
        self.AC_voltage(print_table=print_table)
        self.AC_lines_current(print_table=print_table)
        self.AC_lines_power(print_table=print_table)
        self.Slack_AC(print_table=print_table)
        self.Power_loss_AC(print_table=print_table)

    def All_DC(self, print_table=True):

        if self.Grid.nconv != 0:
            self.Converter(print_table=print_table)

        self.DC_bus(print_table=print_table)

        self.DC_lines_current(print_table=print_table)
        self.DC_lines_power(print_table=print_table)
        self.Slack_DC(print_table=print_table)
        self.Power_loss_DC(print_table=print_table)

    def Slack_All(self, print_table=True):
        rows = []
        for i in range(self.Grid.Num_Grids_AC):
            for node in self.Grid.Grids_AC[i]:
                if node.type == 'Slack':
                    rows.append({"Grid": f'AC Grid {i+1}', "Slack node": node.name})
        for i in range(self.Grid.Num_Grids_DC):
            for node in self.Grid.Grids_DC[i]:
                if node.type == 'Slack':
                    rows.append({"Grid": f'DC Grid {i+1}', "Slack node": node.name})

        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Grid", "Slack node"])
        self.tables["Slack_All"] = df

        if print_table:
            print('--------------')
            print('Slack nodes')
            table = pt()
            table.field_names = ["Grid", "Slack node"]
            for _, row in df.iterrows():
                table.add_row([row["Grid"], row["Slack node"]])
            print(table)

        return df

    def Slack_AC(self, print_table=True):
        rows = []
        for i in range(self.Grid.Num_Grids_AC):
            for node in self.Grid.Grids_AC[i]:
                if node.type == 'Slack':
                    rows.append({"Grid": f'AC Grid {i+1}', "Slack node": node.name})

        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Grid", "Slack node"])
        self.tables["Slack_AC"] = df

        if print_table:
            print('--------------')
            print('Slack nodes')
            table = pt()
            table.field_names = ["Grid", "Slack node"]
            for _, row in df.iterrows():
                table.add_row([row["Grid"], row["Slack node"]])
            print(table)

        return df

    def Slack_DC(self, print_table=True):
        rows = []
        for i in range(self.Grid.Num_Grids_DC):
            for node in self.Grid.Grids_DC[i]:
                if node.type == 'Slack':
                    rows.append({"Grid": f'DC Grid {i+1}', "Slack node": node.name})

        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Grid", "Slack node"])
        self.tables["Slack_DC"] = df

        if print_table:
            print('--------------')
            print('Slack nodes')
            if df.empty:
                print("No DC nodes are set as Slack")
            else:
                table = pt()
                table.field_names = ["Grid", "Slack node"]
                for _, row in df.iterrows():
                    table.add_row([row["Grid"], row["Slack node"]])
                print(table)

        return df


    def Power_loss(self, print_table=True):
        rows = []
        generation=0 
        grid_loads = 0
        tot=0

        # Reset per-call cached loading accumulators.
        # This method updates `Grid.load_grid_*` via `+=`, so without resetting,
        # repeated OPF calls on the same Grid will accumulate and can push
        # "Load %" above 100%.
        if getattr(self.Grid, "load_grid_AC", None) is not None and self.Grid.Num_Grids_AC > 0:
            self.Grid.load_grid_AC = np.zeros(self.Grid.Num_Grids_AC)
        if getattr(self.Grid, "load_grid_DC", None) is not None and self.Grid.Num_Grids_DC > 0:
            self.Grid.load_grid_DC = np.zeros(self.Grid.Num_Grids_DC)
        
        if self.Grid.nodes_AC != []:
            if self.Grid.OPF_run:
                P_AC = np.vstack([node.PGi+sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                                        +sum(gen.PGen for gen in node.connected_gen if gen.PGen >0) for node in self.Grid.nodes_AC])

                Q_AC = np.vstack([node.QGi+sum(gen.QGen for gen in node.connected_gen) for node in self.Grid.nodes_AC])
            else:
                P_AC = np.vstack([node.PGi+sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                                        +sum(gen.Pset for gen in node.connected_gen if gen.Pset >0) for node in self.Grid.nodes_AC])
                Q_AC = np.vstack([node.QGi+sum(gen.Qset for gen in node.connected_gen) for node in self.Grid.nodes_AC])
            
            for node in self.Grid.nodes_AC:
                if not self.Grid.OPF_run and node.type == 'Slack':
                      ps = node.P_s.item() if hasattr(node.P_s, 'item') else node.P_s
                      net_power = node.P_INJ-ps+node.PLi
                      if net_power >0:
                        PGi = net_power
                      else:
                        PGi = 0
                        grid_loads+=abs(net_power)*self.Grid.S_base
    
                else:
                      PGi = P_AC[node.nodeNumber].item()
                generation += PGi*self.Grid.S_base      
                if self.Grid.OPF_run:
                    grid_loads += (node.PLi-sum(gen.PGen for gen in node.connected_gen if gen.PGen <0))*self.Grid.S_base
                else:
                    grid_loads += (node.PLi-sum(gen.Pset for gen in node.connected_gen if gen.Pset <0))*self.Grid.S_base

            self.lossP_AC = np.zeros(self.Grid.Num_Grids_AC)
            effective_rating_AC = np.zeros(self.Grid.Num_Grids_AC)
            
            for line in self.Grid.lines_AC:
                node = line.fromNode
                G = self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber]
                Ploss = np.real(line.loss)*self.Grid.S_base
            
                Sfrom = abs(line.fromS)*self.Grid.S_base
                Sto   = abs(line.toS)*self.Grid.S_base

                load = max(Sfrom, Sto)
                
                self.Grid.load_grid_AC[G] += load
                effective_rating_AC[G] += line.capacity_MVA
                
                self.lossP_AC[G] += Ploss

            
            for line in self.Grid.lines_AC_exp:
                if line.np_line>0.01:
                    node = line.fromNode
                    G = self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber]
                    Ploss = np.real(line.loss)*self.Grid.S_base
                    
                    Sfrom = abs(line.fromS)*self.Grid.S_base
                    Sto   = abs(line.toS)*self.Grid.S_base
    
                    load = max(Sfrom, Sto)
                    
                    self.Grid.load_grid_AC[G] += load
                    effective_rating_AC[G] += line.capacity_MVA
                    
                    self.lossP_AC[G] += Ploss

            for line in self.Grid.lines_AC_tf:
                node = line.fromNode
                G = self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber]
                Ploss = np.real(line.loss)*self.Grid.S_base
                
                Sfrom = abs(line.fromS)*self.Grid.S_base
                Sto   = abs(line.toS)*self.Grid.S_base

                load = max(Sfrom, Sto)
                
                self.Grid.load_grid_AC[G] += load
                effective_rating_AC[G] += line.capacity_MVA
                
                self.lossP_AC[G] += Ploss

            for line in (self.Grid.lines_AC_rec + self.Grid.lines_AC_ct):
                node = line.fromNode
                G = self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber]
                Ploss = np.real(line.loss)*self.Grid.S_base
                
                Sfrom = abs(line.fromS)*self.Grid.S_base
                Sto   = abs(line.toS)*self.Grid.S_base

                load = max(Sfrom, Sto)
                
                self.Grid.load_grid_AC[G] += load
                effective_rating_AC[G] += line.capacity_MVA
                
                self.lossP_AC[G] += Ploss

           
            
            for g in range(self.Grid.Num_Grids_AC):
                if effective_rating_AC[g]!=0:
                    gload=self.Grid.load_grid_AC[g]/effective_rating_AC[g]*100
                else:
                    gload=0
                rows.append({
                    "Grid": f'AC Grid {g+1}',
                    "Power Loss (MW)": np.round(self.lossP_AC[g], decimals=self.dec),
                    "Load %": np.round(gload, decimals=self.dec)
                })
                tot += self.lossP_AC[g]

        if self.Grid.nodes_DC != []:
            for node in self.Grid.nodes_DC:
                generation+= (node.PGi
                              +sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                              +sum(gen.PGen for gen in node.connected_gen if gen.PGen >0))*self.Grid.S_base
                grid_loads += node.PLi*self.Grid.S_base


            self.lossP_DC = np.zeros(self.Grid.Num_Grids_DC)

            for line in self.Grid.lines_DC:
                node = line.fromNode
                G = self.Grid.Graph_node_to_Grid_index_DC[node.nodeNumber]

                Ploss = np.real(line.loss)*self.Grid.S_base
                
                self.lossP_DC[G] += Ploss
                
                       
                i = line.fromNode.nodeNumber
                j = line.toNode.nodeNumber
                p_to = self.Grid.Pij_DC[j, i]*self.Grid.S_base
                p_from = self.Grid.Pij_DC[i, j]*self.Grid.S_base

                load = max(p_to, p_from)
                
                self.Grid.load_grid_DC[G] += load
                
                
            for g in range(self.Grid.Num_Grids_DC):
                gload=self.Grid.load_grid_DC[g]/self.Grid.rating_grid_DC[g]*100
                rows.append({
                    "Grid": f'DC Grid {g+1}',
                    "Power Loss (MW)": np.round(self.lossP_DC[g], decimals=self.dec),
                    "Load %": np.round(gload, decimals=self.dec)
                })
                tot += self.lossP_DC[g]

        if self.Grid.Converters_ACDC != []:
            P_loss_ACDC = 0
            for conv in self.Grid.Converters_ACDC:
                P_loss_ACDC += (conv.P_loss_tf+conv.P_loss)*self.Grid.S_base
                tot += (conv.P_loss_tf+conv.P_loss)*self.Grid.S_base
         
            rows.append({
                "Grid": 'AC DC Converters',
                "Power Loss (MW)": np.round(P_loss_ACDC, decimals=self.dec),
                "Load %": ""
            })


        eff = grid_loads/generation*100
        
        rows.append({
            "Grid": "Total loss",
            "Power Loss (MW)": np.round(tot, decimals=self.dec),
            "Load %": ""
        })
        rows.append({"Grid": "     ", "Power Loss (MW)": "", "Load %": ""})
        rows.append({
            "Grid": "Generation",
            "Power Loss (MW)": np.round(generation, decimals=self.dec),
            "Load %": ""
        })
        rows.append({
            "Grid": "Load",
            "Power Loss (MW)": np.round(grid_loads, decimals=self.dec),
            "Load %": ""
        })
        rows.append({
            "Grid": "Efficiency",
            "Power Loss (MW)": f'{np.round(eff, decimals=self.dec)}%',
            "Load %": ""
        })

        df = pd.DataFrame(rows)
        self.tables["Power_loss"] = df

        if print_table:
            print('--------------')
            print('Power loss')
            table = pt()
            table.field_names = ["Grid", "Power Loss (MW)", "Load %"]
            for _, row in df.iterrows():
                table.add_row([row["Grid"], row["Power Loss (MW)"], row["Load %"]])
            print(table)

        return df

    def Power_loss_AC(self, print_table=True):
        rows = []
        self.lossP_AC = np.zeros(self.Grid.Num_Grids_AC)
        for line in self.Grid.lines_AC:
            node = line.fromNode
            G = self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber]
            Ploss = np.real(line.loss)*self.Grid.S_base
            
            self.lossP_AC[G] += Ploss

        tot = 0
        for g in range(self.Grid.Num_Grids_AC):
            rows.append({
                "Grid": f'AC Grid {g+1}',
                "Power Loss (MW)": np.round(self.lossP_AC[g], decimals=self.dec)
            })
            tot += self.lossP_AC[g]

        rows.append({
            "Grid": "Total loss",
            "Power Loss (MW)": np.round(tot, decimals=self.dec)
        })

        df = pd.DataFrame(rows)
        self.tables["Power_loss_AC"] = df

        if print_table:
            print('--------------')
            print('Power loss AC')
            table = pt()
            table.field_names = ["Grid", "Power Loss (MW)"]
            for _, row in df.iterrows():
                table.add_row([row["Grid"], row["Power Loss (MW)"]])
            print(table)

        return df

    def Power_loss_DC(self, print_table=True):
        rows = []

        self.lossP_DC = np.zeros(self.Grid.Num_Grids_DC)

        for line in self.Grid.lines_DC:
            node = line.fromNode
            G = self.Grid.Graph_node_to_Grid_index_DC[node.nodeNumber]

            Ploss = np.real(line.loss)*self.Grid.S_base

            self.lossP_DC[G] += Ploss
        tot = 0

        for g in range(self.Grid.Num_Grids_DC):
            rows.append({
                "Grid": f'DC Grid {g+1}',
                "Power Loss (MW)": np.round(self.lossP_DC[g], decimals=self.dec)
            })
            tot += self.lossP_DC[g]

        rows.append({
            "Grid": "Total loss",
            "Power Loss (MW)": np.round(tot, decimals=self.dec)
        })

        df = pd.DataFrame(rows)
        self.tables["Power_loss_DC"] = df

        if print_table:
            print('--------------')
            print('Power loss DC')
            table = pt()
            table.field_names = ["Grid", "Power Loss (MW)"]
            for _, row in df.iterrows():
                table.add_row([row["Grid"], row["Power Loss (MW)"]])
            print(table)

        return df

    def DC_bus(self, print_table=True):

        if self.Grid.OPF_run:
            P_DC = np.vstack([node.PGi+sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                              + sum(gen.PGen for gen in node.connected_gen) for node in self.Grid.nodes_DC])
        else:
            P_DC = np.vstack([node.PGi+sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                              + sum(gen.Pset for gen in node.connected_gen) for node in self.Grid.nodes_DC])

        rows = []
        base = self.Grid.S_base

        for g in range(self.Grid.Num_Grids_DC):
            for node in self.Grid.nodes_DC:
                if self.Grid.Graph_node_to_Grid_index_DC[node.nodeNumber] != g:
                    continue
                # Preserve original slack-node adjustment logic
                if not self.Grid.OPF_run and node.type == 'Slack' and self.Grid.nconv == 0:
                    if node.P_INJ > 0:
                        node.PGi = node.P_INJ
                    else:
                        node.PLi = abs(node.P_INJ)
                conv = np.round(node.Pconv*base, decimals=self.dec)
                rows.append({
                    "Node": node.name,
                    "Power Gen (MW)": np.round(P_DC[node.nodeNumber].item()*base, decimals=self.dec),
                    "Power Load (MW)": np.round(node.PLi*base, decimals=self.dec),
                    "Power Converter ACDC (MW)": conv,
                    "Power Converter DCDC (MW)": np.round(node.PconvDC*base, decimals=self.dec),
                    "Power injected (MW)": np.round(node.P_INJ*base, decimals=self.dec),
                    "Voltage (pu)": np.round(node.V, decimals=self.dec),
                    "Grid": g+1
                })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=[
                "Node", "Power Gen (MW)", "Power Load (MW)", "Power Converter ACDC (MW)",
                "Power Converter DCDC (MW)", "Power injected (MW)", "Voltage (pu)", "Grid"
            ]
        )

        self.tables["DC_bus"] = df_all

        if print_table:
            print('--------------')
            print('Results DC')
            print('')
            for g in range(self.Grid.Num_Grids_DC):
                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue
                print(f'Grid DC {g+1}')
                table = pt()
                table.field_names = [
                    "Node", "Power Gen (MW)", "Power Load (MW)", "Power Converter ACDC (MW)",
                    "Power Converter DCDC (MW)", "Power injected (MW)", "Voltage (pu)"
                ]
                for _, row in df_grid.iterrows():
                    table.add_row([
                        row["Node"],
                        row["Power Gen (MW)"],
                        row["Power Load (MW)"],
                        row["Power Converter ACDC (MW)"],
                        row["Power Converter DCDC (MW)"],
                        row["Power injected (MW)"],
                        row["Voltage (pu)"],
                    ])
                print(table)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/DC_bus.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all

    def AC_Powerflow(self, Grid=None, print_table=True):
        # Build combined DataFrame for all AC nodes
        rows = []

        if self.Grid.OPF_run:
            # During OPF, the optimized dispatch is exported into:
            # - node.PGi_opt / node.QGi_opt  (flexible generators, already bounded by np_gen)
            # - node.PGi_ren / node.QGi_ren (renewables with np_rsgen and curtailment via OPF)
            #
            # Using `rs.PGi_ren*rs.gamma` would ignore `np_rsgen` because `rs.PGi_ren`
            # represents available resource (PRGi_available) rather than the OPF-selected
            # renewable units.
            P_AC = np.vstack([node.PGi + node.PGi_ren + node.PGi_opt for node in self.Grid.nodes_AC])
            Q_AC = np.vstack([node.QGi + node.QGi_ren + node.QGi_opt for node in self.Grid.nodes_AC])
        else:
            P_AC = np.vstack([node.PGi+sum(rs.PGi_ren*rs.gamma for rs in node.connected_RenSource)
                              + sum(gen.Pset for gen in node.connected_gen) for node in self.Grid.nodes_AC])
            Q_AC = np.vstack([node.QGi+sum(gen.Qset for gen in node.connected_gen) for node in self.Grid.nodes_AC])

        has_dc = (self.Grid.nodes_DC is not None) and (self.Grid.nodes_DC != [])

        for g in range(self.Grid.Num_Grids_AC):
            for node in self.Grid.nodes_AC:
                if self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber] != g:
                    continue

                PGi = P_AC[node.nodeNumber].item()
                QGi = Q_AC[node.nodeNumber].item()

                if not self.Grid.OPF_run:
                    if node.type == 'Slack':
                        ps = node.P_s.item() if hasattr(node.P_s, 'item') else node.P_s
                        PGi = node.P_INJ-ps + node.PLi
                        QGi = node.Q_INJ-node.Q_s-node.Q_s_fx+node.QLi
                    if node.type == 'PV':
                        QGi = node.Q_INJ-(node.Q_s+node.Q_s_fx)+node.QLi

                base = self.Grid.S_base
                common_data = {
                    "Node": node.name,
                    "Power Gen (MW)": np.round(PGi*base, decimals=self.dec),
                    "Reactive Gen (MVAR)": np.round(QGi*base, decimals=self.dec),
                    "Power Load (MW)": np.round(node.PLi*base, decimals=self.dec),
                    "Reactive Load (MVAR)": np.round(node.QLi*base, decimals=self.dec),
                    "Power injected  (MW)": np.round(node.P_INJ*base, decimals=self.dec),
                    "Reactive injected  (MVAR)": np.round(node.Q_INJ*base, decimals=self.dec),
                    "Grid": g+1,
                }

                if has_dc:
                    # Add converter-related columns
                    common_data["Power converters DC(MW)"] = np.round(node.P_s*base, decimals=self.dec).item()
                    common_data["Reactive converters DC (MVAR)"] = np.round(
                        (node.Q_s+node.Q_s_fx)*base, decimals=self.dec
                    ).item()

                rows.append(common_data)

        if not rows:
            df_all = pd.DataFrame()
        else:
            df_all = pd.DataFrame(rows)

        # Register in central tables dict
        self.tables["AC_Powerflow"] = df_all

        # PrettyTable printing, preserving per-grid layout
        if print_table:
            print('--------------')
            print('Results AC power')
            print('')
            for g in range(self.Grid.Num_Grids_AC):
                if isinstance(Grid, int) and Grid != (g+1):
                    continue

                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue

                print(f'Grid AC {g+1}')
                table = pt()

                if not has_dc:
                    table.field_names = [
                        "Node",
                        "Power Gen (MW)",
                        "Reactive Gen (MVAR)",
                        "Power Load (MW)",
                        "Reactive Load (MVAR)",
                        "Power injected  (MW)",
                        "Reactive injected  (MVAR)",
                    ]
                    for _, row in df_grid.iterrows():
                        table.add_row([
                            row["Node"],
                            row["Power Gen (MW)"],
                            row["Reactive Gen (MVAR)"],
                            row["Power Load (MW)"],
                            row["Reactive Load (MVAR)"],
                            row["Power injected  (MW)"],
                            row["Reactive injected  (MVAR)"],
                        ])
                else:
                    table.field_names = [
                        "Node",
                        "Power Gen (MW)",
                        "Reactive Gen (MVAR)",
                        "Power Load (MW)",
                        "Reactive Load (MVAR)",
                        "Power converters DC(MW)",
                        "Reactive converters DC (MVAR)",
                        "Power injected  (MW)",
                        "Reactive injected  (MVAR)",
                    ]
                    for _, row in df_grid.iterrows():
                        table.add_row([
                            row["Node"],
                            row["Power Gen (MW)"],
                            row["Reactive Gen (MVAR)"],
                            row["Power Load (MW)"],
                            row["Reactive Load (MVAR)"],
                            row["Power converters DC(MW)"],
                            row["Reactive converters DC (MVAR)"],
                            row["Power injected  (MW)"],
                            row["Reactive injected  (MVAR)"],
                        ])

                print(table)

        # CSV export (backwards compatible) when requested
        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/AC_Powerflow.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all

    def AC_voltage(self, print_table=True):
        rows = []

        for g in range(self.Grid.Num_Grids_AC):
            for node in self.Grid.nodes_AC:
                if self.Grid.Graph_node_to_Grid_index_AC[node.nodeNumber] == g:
                    rows.append({
                        "Bus": node.name,
                        "Voltage (pu)": np.round(node.V, decimals=self.dec),
                        "Voltage angle (deg)": np.round(np.degrees(node.theta), decimals=self.dec),
                        "Grid": g+1
                    })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Bus", "Voltage (pu)", "Voltage angle (deg)", "Grid"]
        )

        self.tables["AC_voltage"] = df_all

        if print_table:
            print('--------------')
            print('Results AC bus voltage')
            print('')
            for g in range(self.Grid.Num_Grids_AC):
                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue
                print(f'Grid AC {g+1}')
                table = pt()
                table.field_names = ["Bus", "Voltage (pu)", "Voltage angle (deg)"]
                for _, row in df_grid.iterrows():
                    table.add_row([
                        row["Bus"],
                        row["Voltage (pu)"],
                        row["Voltage angle (deg)"],
                    ])
                print(table)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/AC_voltage.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all

    def AC_lines_current(self, print_table=True):
        rows = []

        for g in range(self.Grid.Num_Grids_AC):
            for line in self.Grid.lines_AC:
                if self.Grid.Graph_line_to_Grid_index_AC[line] == g:
                    i = line.fromNode.nodeNumber
                    j = line.toNode.nodeNumber
                    I_base = self.Grid.S_base/line.kV_base

                    i_from = line.i_from*I_base/np.sqrt(3)

                    i_to = line.i_to*I_base/np.sqrt(3)
                    
                    load = line.loading
                    rows.append({
                        "Line": line.name,
                        "Line number": line.lineNumber,
                        "From bus": line.fromNode.name,
                        "To bus": line.toNode.name,
                        "i from (kA)": np.round(i_from, decimals=self.dec),
                        "i to (kA)": np.round(i_to, decimals=self.dec),
                        "Loading %": np.round(load, decimals=self.dec),
                        # Display the same capacity used inside `line.loading` (np-dependent for exp lines).
                        "Capacity [MVA]": np.round(line.capacity_MVA, decimals=self.dec),
                        "Grid": g+1
                    })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Line", "Line number", "From bus", "To bus",
                     "i from (kA)", "i to (kA)", "Loading %", "Capacity [MVA]", "Grid"]
        )

        # Skip saving/printing if the table is effectively empty
        effective_empty = df_all.empty or df_all.drop(columns=["Grid"], errors="ignore").isna().all().all()
        if not effective_empty:
            self.tables["AC_lines_current"] = df_all

            if print_table:
                print('--------------')
                print('Results AC Lines Currents')
                for g in range(self.Grid.Num_Grids_AC):
                    df_grid = df_all[df_all["Grid"] == (g+1)]
                    if df_grid.empty:
                        continue
                    print(f'Grid AC {g+1}')
                    tablei = pt()
                    tablei.field_names = ["Line", "Line number", "From bus", "To bus",
                                          "i from (kA)", "i to (kA)", "Loading %", "Capacity [MVA]"]
                    for _, row in df_grid.iterrows():
                        tablei.add_row([
                            row["Line"],
                            row["Line number"],
                            row["From bus"],
                            row["To bus"],
                            row["i from (kA)"],
                            row["i to (kA)"],
                            row["Loading %"],
                            row["Capacity [MVA]"],
                        ])
                    print(tablei)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/AC_line_current.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all

    def AC_exp_lines_power(self, print_table=True):

        rows = []

        for g in range(self.Grid.Num_Grids_AC):
            loss = 0
            loading = 0
            counter = 0
            for line in self.Grid.lines_AC_exp:
                if line.np_line > 0.01 and self.Grid.Graph_line_to_Grid_index_AC[line] == g:
                    p_from = np.real(line.fromS)*self.Grid.S_base
                    Q_from = np.imag(line.fromS)*self.Grid.S_base
                    p_to = np.real(line.toS)*self.Grid.S_base
                    Q_to = np.imag(line.toS)*self.Grid.S_base
                    Ploss = np.real(line.loss)*self.Grid.S_base
                    Qloss = np.imag(line.loss)*self.Grid.S_base
                    load = line.loading
                    rows.append({
                        "Line": line.name,
                        "Line number": line.lineNumber,
                        "From bus": line.fromNode.name,
                        "To bus": line.toNode.name,
                        "P from (MW)": np.round(p_from, decimals=self.dec),
                        "Q from (MVAR)": np.round(Q_from, decimals=self.dec),
                        "P to (MW)": np.round(p_to, decimals=self.dec),
                        "Q to (MW)": np.round(Q_to, decimals=self.dec),
                        "Power loss (MW)": np.round(Ploss, decimals=self.dec),
                        "Q loss (MVAR)": np.round(Qloss, decimals=self.dec),
                        "Loading %": np.round(load, decimals=self.dec),
                        "Grid": g+1
                    })
                    loss += Ploss
                    loading += load
                    counter += 1
            for line in self.Grid.lines_AC_rec:
                if self.Grid.Graph_line_to_Grid_index_AC[line] == g:
                    p_from = np.real(line.fromS)*self.Grid.S_base
                    Q_from = np.imag(line.fromS)*self.Grid.S_base
                    p_to = np.real(line.toS)*self.Grid.S_base
                    Q_to = np.imag(line.toS)*self.Grid.S_base
                    Ploss = np.real(line.loss)*self.Grid.S_base
                    Qloss = np.imag(line.loss)*self.Grid.S_base
                    load = line.loading
                    rows.append({
                        "Line": line.name,
                        "Line number": line.lineNumber,
                        "From bus": line.fromNode.name,
                        "To bus": line.toNode.name,
                        "P from (MW)": np.round(p_from, decimals=self.dec),
                        "Q from (MVAR)": np.round(Q_from, decimals=self.dec),
                        "P to (MW)": np.round(p_to, decimals=self.dec),
                        "Q to (MW)": np.round(Q_to, decimals=self.dec),
                        "Power loss (MW)": np.round(Ploss, decimals=self.dec),
                        "Q loss (MVAR)": np.round(Qloss, decimals=self.dec),
                        "Loading %": np.round(load, decimals=self.dec),
                        "Grid": g+1
                    })
                    loss += Ploss
                    loading += load
                    counter += 1
            for line in self.Grid.lines_AC_ct:
                if line.active_config >= 0 and self.Grid.Graph_line_to_Grid_index_AC[line] == g:
                    p_from = np.real(line.fromS)*self.Grid.S_base
                    Q_from = np.imag(line.fromS)*self.Grid.S_base
                    p_to = np.real(line.toS)*self.Grid.S_base
                    Q_to = np.imag(line.toS)*self.Grid.S_base
                    Ploss = np.real(line.loss)*self.Grid.S_base
                    Qloss = np.imag(line.loss)*self.Grid.S_base
                    load = line.loading
                    rows.append({
                        "Line": line.name,
                        "Line number": line.lineNumber,
                        "From bus": line.fromNode.name,
                        "To bus": line.toNode.name,
                        "P from (MW)": np.round(p_from, decimals=self.dec),
                        "Q from (MVAR)": np.round(Q_from, decimals=self.dec),
                        "P to (MW)": np.round(p_to, decimals=self.dec),
                        "Q to (MW)": np.round(Q_to, decimals=self.dec),
                        "Power loss (MW)": np.round(Ploss, decimals=self.dec),
                        "Q loss (MVAR)": np.round(Qloss, decimals=self.dec),
                        "Loading %": np.round(load, decimals=self.dec),
                        "Grid": g+1
                    })
                    loss += Ploss
                    loading += load
                    counter += 1
            avg_loading = np.round(loading / counter, decimals=self.dec) if counter > 0 else np.nan
            rows.append({
                        "Line": "Total",
                        "Line number": "",
                        "From bus": "",
                        "To bus": "",
                        "P from (MW)": "",
                        "Q from (MVAR)": "",
                        "P to (MW)": "",
                        "Q to (MW)": "",
                        "Power loss (MW)": np.round(loss, decimals=self.dec),
                        "Q loss (MVAR)": np.round(loss, decimals=self.dec),
                        "Loading %": avg_loading,
                        "Grid": g+1
                    })
        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=[
                "Line", "Line number", "From bus", "To bus",
                "P from (MW)", "Q from (MVAR)", "P to (MW)", "Q to (MW)",
                "Power loss (MW)", "Q loss (MVAR)", "Loading %", "Grid"
            ]
        )

        self.tables["AC_exp_lines_power"] = df_all

        if print_table:
            print('--------------')
            print('Results AC Expansion Lines power')
            for g in range(self.Grid.Num_Grids_AC):
                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue
                print(f'Grid AC {g+1}')
                tablep = pt()
                tablep.field_names = ["Line", "Line number", "From bus", "To bus",
                                      "P from (MW)", "Q from (MVAR)", "P to (MW)", "Q to (MW)",
                                      "Power loss (MW)", "Q loss (MVAR)", "Loading %"]
                for _, row in df_grid.iterrows():
                    tablep.add_row([
                        row["Line"],
                        row["Line number"],
                        row["From bus"],
                        row["To bus"],
                        row["P from (MW)"],
                        row["Q from (MVAR)"],
                        row["P to (MW)"],
                        row["Q to (MW)"],
                        row["Power loss (MW)"],
                        row["Q loss (MVAR)"],
                        row["Loading %"],
                    ])
                print(tablep)

        
        return df_all


    def AC_lines_power(self, Grid=None, print_table=True):
        
        rows = []
        base = self.Grid.S_base

        for g in range(self.Grid.Num_Grids_AC):
            for line in self.Grid.lines_AC:
                if self.Grid.Graph_line_to_Grid_index_AC[line] != g:
                    continue
                p_from = np.real(line.fromS)*base
                Q_from = np.imag(line.fromS)*base
                p_to = np.real(line.toS)*base
                Q_to = np.imag(line.toS)*base
                Ploss = np.real(line.loss)*base
                Qloss = np.imag(line.loss)*base
                rows.append({
                    "Line": line.name,
                    "Line number": line.lineNumber,
                    "From bus": line.fromNode.name,
                    "To bus": line.toNode.name,
                    "P from (MW)": np.round(p_from, decimals=self.dec),
                    "Q from (MVAR)": np.round(Q_from, decimals=self.dec),
                    "P to (MW)": np.round(p_to, decimals=self.dec),
                    "Q to (MW)": np.round(Q_to, decimals=self.dec),
                    "Power loss (MW)": np.round(Ploss, decimals=self.dec),
                    "Q loss (MVAR)": np.round(Qloss, decimals=self.dec),
                    "Grid": g+1
                })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=[
                "Line", "Line number", "From bus", "To bus",
                "P from (MW)", "Q from (MVAR)", "P to (MW)", "Q to (MW)",
                "Power loss (MW)", "Q loss (MVAR)", "Grid"
            ]
        )

        # Skip saving/printing if the table is effectively empty
        effective_empty = df_all.empty or df_all.drop(columns=["Grid"], errors="ignore").isna().all().all()
        if not effective_empty:
            self.tables["AC_lines_power"] = df_all

            if print_table:
                print('--------------')
                print('Results AC Lines power')
                for g in range(self.Grid.Num_Grids_AC):
                    if isinstance(Grid, int) and Grid != (g+1):
                        continue
                    df_grid = df_all[df_all["Grid"] == (g+1)]
                    if df_grid.empty:
                        continue
                    print(f'Grid AC {g+1}')
                    tablep = pt()
                    tablep.field_names = ["Line", "From bus", "To bus",
                                          "P from (MW)", "Q from (MVAR)", "P to (MW)", "Q to (MW)",
                                          "Power loss (MW)", "Q loss (MVAR)"]
                    for _, row in df_grid.iterrows():
                        tablep.add_row([
                            row["Line"],
                            row["From bus"],
                            row["To bus"],
                            row["P from (MW)"],
                            row["Q from (MVAR)"],
                            row["P to (MW)"],
                            row["Q to (MW)"],
                            row["Power loss (MW)"],
                            row["Q loss (MVAR)"],
                        ])
                    print(tablep)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/AC_line_power.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all
    def Ext_gen(self, print_table=True):
        rows = []
        Ptot=0
        Qtot=0
        Pabs=0
        Qabs=0
        Stot=0
        Ltot=0
        costtot=0
        for gen in self.Grid.Generators:
          if gen.np_gen>0.001:  
            n_units = float(gen.np_gen)
            Pgi=gen.PGen*self.Grid.S_base
            Qgi=gen.QGen*self.Grid.S_base
            S= np.sqrt(Pgi**2+Qgi**2)
            Pgi_unit = Pgi / n_units
            
            load=gen.loading
            qf=gen.qf
            fc=gen.fc
            cost_unit=(Pgi_unit**2*qf+Pgi_unit*gen.lf+fc)/1000
            cost_total=cost_unit*n_units
           
            rows.append({
                "Generator": gen.name,
                "Node": gen.Node_AC,
                "Num. gen": np.round(gen.np_gen, decimals=self.dec),
                "Power (MW)": np.round(Pgi, decimals=self.dec),
                "Reactive power (MVAR)": np.round(Qgi, decimals=self.dec),
                "Quadratic Price €/MWh^2": np.round(qf, decimals=self.dec),
                "Linear Price €/MWh": np.round(gen.lf, decimals=self.dec),
                "Fixed Cost €/unit": np.round(fc, decimals=self.dec),
                "Loading %": np.round(load, decimals=self.dec),
                "Cost per unit k€": np.round(cost_unit, decimals=0),
                "Total Cost k€": np.round(cost_total, decimals=0)
            })
            Pabs+=abs(Pgi)
            Qabs+=abs(Qgi)
            Ptot+=Pgi
            Qtot+=Qgi
            Stot+=S
            costtot+=cost_total
            Ltot+=gen.capacity_MVA

        for gen in self.Grid.Generators_DC:
          if gen.np_gen>0.001:  
            n_units = float(gen.np_gen)
            Pgi=gen.PGen*self.Grid.S_base
            Pgi_unit = Pgi / n_units
            
            load=gen.loading
            qf=gen.qf
            fc=gen.fc
            cost_unit=(Pgi_unit**2*qf+Pgi_unit*gen.lf+fc)/1000
            cost_total=cost_unit*n_units
           
            rows.append({
                "Generator": gen.name,
                "Node": gen.Node_DC,
                "Num. gen": np.round(gen.np_gen, decimals=self.dec),
                "Power (MW)": np.round(Pgi, decimals=self.dec),
                "Reactive power (MVAR)": "----",
                "Quadratic Price €/MWh^2": np.round(qf, decimals=self.dec),
                "Linear Price €/MWh": np.round(gen.lf, decimals=self.dec),
                "Fixed Cost €/unit": np.round(fc, decimals=self.dec),
                "Loading %": np.round(load, decimals=self.dec),
                "Cost per unit k€": np.round(cost_unit, decimals=0),
                "Total Cost k€": np.round(cost_total, decimals=0)
            })
            Pabs+=abs(Pgi)
            Ptot+=Pgi
            Stot+=Pgi
            costtot+=cost_total
            Ltot+=gen.capacity_MW

        if Ltot !=0:
            load=Stot/Ltot*100
        else:
            load=0
        rows.append({
            "Generator": "Total",
            "Node": "",
            "Num. gen": "",
            "Power (MW)": np.round(Ptot, decimals=self.dec),
            "Reactive power (MVAR)": np.round(Qtot, decimals=self.dec),
            "Quadratic Price €/MWh^2": "",
            "Linear Price €/MWh": "",
            "Fixed Cost €/unit": " ",
            "Loading %": "",
            "Cost per unit k€": "",
            "Total Cost k€": np.round(costtot, decimals=0)
        })
        rows.append({
            "Generator": "Total abs",
            "Node": "",
            "Num. gen": "",
            "Power (MW)": np.round(Pabs, decimals=self.dec),
            "Reactive power (MVAR)": np.round(Qabs, decimals=self.dec),
            "Quadratic Price €/MWh^2": "",
            "Linear Price €/MWh": "",
            "Fixed Cost €/unit": "",
            "Loading %": np.round(load, decimals=self.dec),
            "Cost per unit k€": "",
            "Total Cost k€": ""
        })

        columns = [
            "Generator", "Node", "Num. gen", "Power (MW)", "Reactive power (MVAR)",
            "Quadratic Price €/MWh^2", "Linear Price €/MWh", "Fixed Cost €/unit", "Loading %",
            "Cost per unit k€", "Total Cost k€"
        ]
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=columns)
        if "Num. gen" in df.columns:
            df["Num. gen"] = df["Num. gen"].fillna("")
        self.tables["Ext_gen"] = df

        if print_table:
            print('--------------')
            print('External Generation optimization')
            table = pt()
            table.field_names = columns
            for _, row in df.iterrows():
                table.add_row([row[col] for col in columns])
            print(table)
    
        return df
    
    def Ext_REN(self, print_table=True):
        rows = []
        bp=0
        tcur=0
        totcost=0
        totcurcost=0
        price=0
        for rs in self.Grid.RenSources:
                Pgi=rs.PGi_ren*self.Grid.S_base
                bp+=Pgi
                cur= (1-rs.gamma)*100
                tcur+=Pgi*(1-rs.gamma)
                PGicur=Pgi*(rs.gamma)*rs.np_rsgen
                QGi=rs.QGi_ren*self.Grid.S_base*rs.np_rsgen
                
                if not self.Grid.OnlyGen or self.Grid.OPF_Price_Zones_constraints_used:
                   
                    if rs.connected == 'AC':
                        node_num = self.Grid.rs2node['AC'][rs.rsNumber]
                        node = self.Grid.nodes_AC[node_num]
                        price=node.price
                    else:
                        node_num = self.Grid.rs2node['DC'][rs.rsNumber]
                        node = self.Grid.nodes_DC[node_num]
                        price=node.price
                    cost=PGicur*price/1000
                else:
                    cost=0 
                if self.Grid.CurtCost==False:
                    curcost=0
                else:    
                    curcost= (Pgi-PGicur)*node.price*(self.Grid.sigma)/1000
                rows.append({
                    "Name": rs.name,
                    "Bus": rs.Node,
                    "Num. gen": np.round(rs.np_rsgen, decimals=self.dec),
                    "Base Power (MW)": np.round(Pgi, decimals=self.dec),
                    "Curtailment %": np.round(cur, decimals=self.dec),
                    "Power Injected (MW)": np.round(PGicur, decimals=self.dec),
                    "Reactive Power Injected (MVAR)": np.round(QGi, decimals=self.dec),
                    "Price €/MWh": np.round(price, decimals=self.dec),
                    "Cost k€": np.round(cost, decimals=0),
                    "Curtailment Cost [k€]": np.round(curcost, decimals=0)
                })
                totcost+=cost
                totcurcost+=curcost
        
        PGicur=bp-tcur
        cur=(tcur)/bp*100 if bp != 0 else 0
        
        rows.append({
            "Name": "Total",
            "Bus": "",
            "Num. gen": "",
            "Base Power (MW)": np.round(bp, decimals=self.dec),
            "Curtailment %": np.round(cur, decimals=self.dec),
            "Power Injected (MW)": np.round(PGicur, decimals=self.dec),
            "Reactive Power Injected (MVAR)": "",
            "Price €/MWh": "",
            "Cost k€": np.round(totcost, decimals=0),
            "Curtailment Cost [k€]": np.round(totcurcost, decimals=0)
        })

        df = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Name","Bus", "Num. gen", "Base Power (MW)", "Curtailment %",
                     "Power Injected (MW)","Reactive Power Injected (MVAR)",
                     "Price €/MWh","Cost k€","Curtailment Cost [k€]"]
        )
        self.tables["Ext_REN"] = df

        if print_table:
            print('--------------')
            print('Renewable energy sources')
            table = pt()
            table.field_names = ["Name","Bus", "Num. gen", "Base Power (MW)", "Curtailment %",
                                 "Power Injected (MW)","Reactive Power Injected (MVAR)",
                                 "Price €/MWh","Cost k€","Curtailment Cost [k€]"]
            for _, row in df.iterrows():
                table.add_row([
                    row["Name"],
                    row["Bus"],
                    row["Num. gen"],
                    row["Base Power (MW)"],
                    row["Curtailment %"],
                    row["Power Injected (MW)"],
                    row["Reactive Power Injected (MVAR)"],
                    row["Price €/MWh"],
                    row["Cost k€"],
                    row["Curtailment Cost [k€]"],
                ])
            print(table)

        return df
    def Clustering_results(self, print_table=True):
        self.Clustering_Time_series_statistics()
        for key in self.Grid.Clustering_information:
            if key.startswith('technique_'):
                self.Clustering_technique(key, print_table)
        self.Cluster_representatives(print_table=print_table)

    def Cluster_representatives(self, print_table=True):
        """
        Display cluster representatives (centroids/medoids) for each clustering run.
        Each row is a cluster, columns are the time series features plus Weight and Count.
        """
        if not hasattr(self.Grid, 'Clusters') or not self.Grid.Clusters:
            return pd.DataFrame()

        all_dfs = {}
        for n_clusters, cluster_data in self.Grid.Clusters.items():
            reps = cluster_data.get('Representatives', None)
            if reps is None or not isinstance(reps, pd.DataFrame):
                continue

            df = reps.copy()
            df.insert(0, 'Cluster', range(1, len(df) + 1))

            # Round numeric columns
            numeric_cols = df.select_dtypes(include='number').columns
            df[numeric_cols] = df[numeric_cols].round(self.dec)

            table_name = f"Cluster_Representatives_{n_clusters}"
            self.tables[table_name] = df
            all_dfs[n_clusters] = df

            if print_table:
                print(f'\n--------------')
                print(f'Cluster Representatives (k={n_clusters})')
                print('')
                table = pt()
                table.field_names = list(df.columns)
                for col in table.field_names:
                    table.align[col] = 'r'
                table.align[table.field_names[0]] = 'c'
                for _, row in df.iterrows():
                    table.add_row([row[c] for c in df.columns])
                print(table)

        if len(all_dfs) == 1:
            return list(all_dfs.values())[0]
        return all_dfs
                
    def Clustering_technique(self, key, print_table=True):
        """
        Display clustering results for a specific technique.
        
        Parameters:
        -----------
        key : str
            The key of the clustering technique
        print_table : bool, default=True
            If True, print the statistics table
        """
        technique = key.split('_')[1]
        n_clusters = key.split('_')[2]
        clustering_result = self.Grid.Clustering_information[key]
        
        if print_table:
            # Print in the same format as print_clustering_results
            algorithm_name = clustering_result.get('algorithm', technique)
            print(f"\n{algorithm_name} clustering results:")
            print(f"- Number of clusters: {n_clusters}")
            
            # Print time taken if available
            if 'time taken' in clustering_result:
                print(f"- Time taken: {np.round(clustering_result['time taken'], decimals=self.dec)} seconds")
            
            # Get specific_info and print all key-value pairs
            specific_info = clustering_result.get('specific_info', {})
            for key, value in specific_info.items():
                # Skip derived statistics that are already included
                if key in ["Cluster sizes average", "Cluster sizes std"]:
                    continue
                
                # Format value based on type
                if isinstance(value, list):
                    # Convert numpy types in lists to native Python types
                    formatted_value = [int(v) if isinstance(v, (np.integer, np.int64, np.int32)) 
                                      else float(v) if isinstance(v, (np.floating, np.float64, np.float32))
                                      else v for v in value]
                    print(f"- {key}: {formatted_value}")
                elif isinstance(value, (np.integer, np.int64, np.int32)):
                    print(f"- {key}: {int(value)}")
                elif isinstance(value, (np.floating, np.float64, np.float32)):
                    print(f"- {key}: {np.round(float(value), decimals=self.dec)}")
                elif isinstance(value, float):
                    print(f"- {key}: {np.round(value, decimals=self.dec)}")
                elif isinstance(value, dict):
                    # Handle dict values (like Noise points)
                    if 'count' in value and 'percentage' in value:
                        print(f"- {key}: {value['count']} ({value['percentage']:.{self.dec}f}%)")
                    else:
                        print(f"- {key}: {value}")
                else:
                    print(f"- {key}: {value}")
        
        # Store in tables dict for Excel export
        technique_name = f"Clustering_{technique}_{n_clusters}"
        rows = []
        row_data = {
            "Algorithm": technique,
            "Number of clusters": n_clusters,
            "CoV": clustering_result.get('CoV', None)
        }
        
        # Add specific_info to row
        specific_info = clustering_result.get('specific_info', {})
        for info_key, info_value in specific_info.items():
            if info_key == "Cluster sizes":
                if isinstance(info_value, list):
                    row_data["Cluster sizes (avg)"] = specific_info.get('Cluster sizes average', np.mean(info_value) if len(info_value) > 0 else None)
                    row_data["Cluster sizes (std)"] = specific_info.get('Cluster sizes std', np.std(info_value) if len(info_value) > 0 else None)
            elif info_key not in ["Cluster sizes average", "Cluster sizes std"]:
                if isinstance(info_value, dict):
                    row_data[info_key] = str(info_value)
                else:
                    row_data[info_key] = info_value
        
        rows.append(row_data)
        df = pd.DataFrame(rows)
        self.tables[technique_name] = df
        
        return clustering_result

    def Clustering_Time_series_statistics(self, print_table=True):
        """
        Display time series statistics (Mean, Std, Var, CV) from clustering analysis.
        
        Parameters:
        -----------
        print_table : bool, default=True
            If True, print the statistics table
        """
        if (not hasattr(self.Grid, 'Clustering_information') or 
            self.Grid.Clustering_information is None or 
            'Time_series_statistics' not in self.Grid.Clustering_information):
            if print_table:
                print('--------------')
                print('Time series statistics')
                print('No time series statistics available. Run clustering analysis first.')
            return pd.DataFrame()
        
        df = self.Grid.Clustering_information['Time_series_statistics'].copy()
        
        # Round numeric columns for display
        numeric_cols = ['Mean', 'Std', 'Var', 'CV']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: np.round(x, decimals=self.dec) if isinstance(x, (int, float, np.number)) and pd.notna(x) and np.isfinite(x) else x)
        
        self.tables["Time_series_statistics"] = df
        
        if print_table:
            print('--------------')
            print('Time series statistics (sorted by CV)')
            table = pt()
            table.field_names = ["Name", "Mean", "Std", "Var", "CV"]
            for _, row in df.iterrows():
                # Check if this is a separator row (has string values)
                is_separator = isinstance(row['Mean'], str) or row['Name'] in ['---', 'Not']
                
                if is_separator:
                    # For separator row, use values as-is
                    table.add_row([
                        row['Name'],
                        row['Mean'],
                        row['Std'],
                        row['Var'],
                        row['CV'],
                    ])
                else:
                    # Format numeric values for display using self.dec
                    mean_val = f"{row['Mean']:.{self.dec}f}" if isinstance(row['Mean'], (int, float, np.number)) and pd.notna(row['Mean']) and np.isfinite(row['Mean']) else str(row['Mean'])
                    std_val = f"{row['Std']:.{self.dec}f}" if isinstance(row['Std'], (int, float, np.number)) and pd.notna(row['Std']) and np.isfinite(row['Std']) else str(row['Std'])
                    var_val = f"{row['Var']:.{self.dec}f}" if isinstance(row['Var'], (int, float, np.number)) and pd.notna(row['Var']) and np.isfinite(row['Var']) else str(row['Var'])
                    cv_val = f"{row['CV']:.{self.dec}f}" if isinstance(row['CV'], (int, float, np.number)) and pd.notna(row['CV']) and np.isfinite(row['CV']) else str(row['CV'])
                    
                    table.add_row([
                        row['Name'],
                        mean_val,
                        std_val,
                        var_val,
                        cv_val,
                    ])
            print(table)
        
        
        
        return df
    
    def TEP_multiScenario_res(self, print_table=True):
        if self.Grid.TEP_multiScenario_res is None:
            return None
        
        TEP_multiScenario_res = self.Grid.TEP_multiScenario_res
        PN   = TEP_multiScenario_res['PN']
        SC   = TEP_multiScenario_res['PZ_cost_of_generation']
        curt = TEP_multiScenario_res['curtailment']
        lines= TEP_multiScenario_res['lines']
        conv = TEP_multiScenario_res['converters']
        price= TEP_multiScenario_res['price']

        # Helper to detect "empty" tables (None, empty, or all-NaN)
        def _is_empty(df):
            return (df is None) or df.empty or getattr(df, "isna", lambda: False)().all().all()

        # Build DataFrames with the same headers / first column as the PrettyTable printout,
        # only for non-empty tables, so that Excel exports match the on-screen tables and
        # we avoid saving completely empty sheets.
        if not _is_empty(PN):
            pn_for_excel = PN.fillna('')
            pn_for_excel = pn_for_excel.copy()
            pn_for_excel.insert(0, '', pn_for_excel.index)
            pn_for_excel.columns = [''] + [f'Net price zone power [MW] @ Case:{t}' for t in PN.columns]
            self.tables["TEP_MS_PN"] = pn_for_excel

        if not _is_empty(SC):
            sc_for_excel = SC.fillna('')
            sc_for_excel = sc_for_excel.copy()
            sc_for_excel.insert(0, '', sc_for_excel.index)
            sc_for_excel.columns = [''] + [f'Cost of Generation [k€] @ Case:{t}' for t in SC.columns]
            self.tables["TEP_MS_SC"] = sc_for_excel

        if not _is_empty(price):
            price_for_excel = price.fillna('')
            price_for_excel = price_for_excel.copy()
            price_for_excel.insert(0, '', price_for_excel.index)
            price_for_excel.columns = [''] + [f'Price Zone Price [€/Mwh] @ Case:{t}' for t in price.columns]
            self.tables["TEP_MS_price"] = price_for_excel

        if not _is_empty(curt):
            curt_for_excel = curt.fillna('')
            curt_for_excel = curt_for_excel.copy()
            curt_for_excel.insert(0, '', curt_for_excel.index)
            curt_for_excel.columns = [''] + [f'Curtialment [MW] @ Case:{t}' for t in curt.columns]
            self.tables["TEP_MS_curtailment"] = curt_for_excel

        if not _is_empty(lines):
            lines_for_excel = lines.fillna('')
            lines_for_excel = lines_for_excel.copy()
            lines_for_excel.insert(0, '', lines_for_excel.index)
            lines_for_excel.columns = [''] + [f'Line loading [%] @ Case:{t}' for t in lines.columns]
            self.tables["TEP_MS_lines_loading"] = lines_for_excel

        if not _is_empty(conv):
            conv_for_excel = conv.fillna('')
            conv_for_excel = conv_for_excel.copy()
            conv_for_excel.insert(0, '', conv_for_excel.index)
            conv_for_excel.columns = [''] + [f'Converter loading [%] @ Case:{t}' for t in conv.columns]
            self.tables["TEP_MS_converters_loading"] = conv_for_excel

        if print_table:
            # PN
            if not _is_empty(PN):
                table = pt()
                data = PN.fillna('')
                field_names = [''] + [f'Net price zone power [MW] @ Case:{t}' for t in data.columns]
                table.field_names = field_names
                for index, row in data.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)
            
            # SC
            if not _is_empty(SC):
                table = pt()
                data_SC = SC.fillna('')
                field_names = [''] + [f'Cost of Generation [k€] @ Case:{t}' for t in data_SC.columns]
                table.field_names = field_names
                for index, row in data_SC.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)
            
            # price
            if not _is_empty(price):
                table = pt()
                data_price = price.fillna('')
                field_names = [''] + [f'Price Zone Price [€/Mwh] @ Case:{t}' for t in data_price.columns]
                table.field_names = field_names
                for index, row in data_price.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)
            
            # curtailment
            if not _is_empty(curt):
                table = pt()
                data_curt = curt.fillna('')
                field_names = [''] + [f'Curtialment [MW] @ Case:{t}' for t in data_curt.columns]
                table.field_names = field_names
                for index, row in data_curt.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)
            
            # lines
            if not _is_empty(lines):
                table = pt()
                data_lines = lines.fillna('')
                field_names = [''] + [f'Line loading [%] @ Case:{t}' for t in data_lines.columns]
                table.field_names = field_names
                for index, row in data_lines.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)
            
            # converters
            if not _is_empty(conv):
                table = pt()
                data_conv = conv.fillna('')
                field_names = [''] + [f'Converter loading [%] @ Case:{t}' for t in data_conv.columns]
                table.field_names = field_names
                for index, row in data_conv.iterrows():
                    table.add_row([index] + row.tolist())
                print(table)

        # Return a dict of the underlying DataFrames for convenience
        return {
            "PN": PN,
            "SC": SC,
            "curtailment": curt,
            "lines": lines,
            "converters": conv,
            "price": price,
        }

    def TEP_N(self, print_table=True):
        rows = []
        tot=0
        
        for l in self.Grid.lines_AC_exp:
            if l.np_line_opf:
                if (l.np_line-l.np_line_b)>0.01:
                    element= l.name
                    ini= l.np_line_b
                    opt=l.np_line
                    pr= opt*l.MVA_rating
                    cost=(opt-ini)*l.base_cost
                    tot+=cost
                    maxn=l.np_line_max
                    rows.append([element, "AC Line" ,ini, np.round(opt, decimals=2),maxn,
                                 float(np.round(pr, decimals=0)), float(cost)])
        
        for l in self.Grid.lines_AC_rec:
            if l.rec_line_opf:
                if l.rec_branch:
                    element= l.name
                    ini= 0
                    opt= l.rec_branch
                    pr= l.MVA_rating_new
                    cost= l.base_cost
                    tot+=cost
                    rows.append([element, "AC Upgrade" ,"", "","",
                                 float(np.round(pr, decimals=0)), float(cost)])
        for l in self.Grid.lines_AC_ct:
            if l.array_opf and l.active_config >=0:
                element= l.name
                ini= l.cable_types[l.ini_active_config] if l.ini_active_config >= 0 else ""
                maxv=l.cable_types[l.max_active_config]
                ct=l.active_config
                typev=l.cable_types[ct]
                pr= l.MVA_rating
                cost= l.base_cost[ct]
                tot+=cost
                rows.append([element, "AC CT" ,ini, typev, maxv,
                             float(np.round(pr, decimals=0)), float(cost)])

        for l in self.Grid.lines_DC:
            if l.np_line_opf:
                if (l.np_line-l.np_line_b)>0.01:
                    element= l.name
                    ini= l.np_line_b
                    opt=l.np_line
                    pr= opt*l.MW_rating
                    cost=(opt-ini)*l.base_cost
                    tot+=cost
                    maxn=l.np_line_max
                    rows.append([element, "DC Line" ,ini, np.round(opt, decimals=2),maxn,
                                 float(np.round(pr, decimals=0)), float(cost)])
                
        
        for cn in self.Grid.Converters_ACDC:
            if cn.np_conv_opf:
                if (cn.np_conv-cn.np_conv_b)>0.01:
                    element= cn.name
                    ini=cn.np_conv_b
                    opt=cn.np_conv
                    pr=opt*cn.MVA_max
                    cost=(opt-ini)*cn.base_cost
                    tot+=cost
                    maxn=cn.np_conv_max
                    rows.append([element, "ACDC Conv" ,ini,np.round(opt, decimals=2),maxn,
                                 float(np.round(pr, decimals=0)), float(cost)])
        

        for gen in self.Grid.Generators:
            if gen.np_gen_opf:
                if (gen.np_gen-gen.np_gen_b)>0.01:
                    element= gen.name
                    ini= gen.np_gen_b
                    opt= gen.np_gen
                    if gen.Max_S is not None:
                        pr= gen.Max_S*gen.np_gen*self.Grid.S_base
                    elif gen.Max_pow_gen !=0:
                        pr= gen.Max_pow_gen*gen.np_gen*self.Grid.S_base
                    else:
                        pr=gen.Max_pow_genR*gen.np_gen*self.Grid.S_base
                    cost= (opt-ini)*gen.base_cost
                    tot+=cost
                    maxn=gen.np_gen_max
                    rows.append([element, "Generator" ,ini,np.round(opt, decimals=2),maxn,
                                 float(np.round(pr, decimals=0)), float(cost)])

        for ren in self.Grid.RenSources:
            if ren.np_rsgen_opf:
                if (ren.np_rsgen-ren.np_rsgen_b)>0.01:
                    element = ren.name
                    ini = ren.np_rsgen_b
                    opt = ren.np_rsgen
                    pr = ren.Max_S * ren.np_rsgen * self.Grid.S_base
                    cost = (opt-ini) * ren.base_cost
                    tot += cost
                    maxn = ren.np_rsgen_max
                    rows.append([element, "Ren Generator", ini, np.round(opt, decimals=2), maxn,
                                 float(np.round(pr, decimals=0)), float(cost)])

        rows.append(["Total", "" ,"","", "", "", float(tot)])

        df = pd.DataFrame(rows, columns=[
            "Element","Type" ,"Initial", "Optimized N","Maximum",
            "Optimized Power Rating [MW]","Expansion Cost [€]"
        ])
        self.tables["TEP_N"] = df
        
        if print_table:
            print('--------------')
            print('Transmission Expansion Problem')
            table = pt()
            table.field_names = ["Element","Type" ,"Initial", "Optimized N","Maximum",
                                 "Optimized Power Rating [MW]","Expansion Cost [€]"]
            for _, row in df.iterrows():
                element, typ, ini, opt, maxn, pr, cost = row
                table.add_row([
                    element,
                    typ,
                    ini,
                    opt,
                    maxn,
                    pr if not isinstance(pr, (int, float)) else int(pr),
                    f"{cost:,.2f}".replace(',', ' ') if pd.notna(cost) else cost,
                ])
            print(table)

        return df

    def TEP_norm(self, print_table=True):
        weights = self.Grid.OPF_obj

        # Keep raw numeric values in the DataFrame; formatting is only for PrettyTable printing
        df = pd.DataFrame.from_dict(weights, orient="index")
        df = df.rename_axis("Objective").reset_index()
        # Ensure consistent column order if keys exist
        cols = ["Objective", "w", "v", "NPV"]
        df = df[cols] if all(c in df.columns for c in cols[1:]) else df

        self.tables["TEP_norm"] = df
        
        if print_table:
            table=pt()
            table.field_names = ["Objective","Weight" ,"Value","Weighted Value","NPV"]
            for _, row in df.iterrows():
                w = row.get("w", 0.0)
                v = row.get("v", 0.0)
                npv = row.get("NPV", 0.0)
                table.add_row([
                    row["Objective"],
                    f"{w:.2f}",
                    f"{v:,.2f}".replace(',', ' '),
                    f"{w*v:,.2f}".replace(',', ' '),
                    f"{npv:,.2f}".replace(',', ' '),
                ])
            print(table)

        return df


    def OBJ_res(self, print_table=True):
        weights = self.Grid.OPF_obj

        # Raw numeric values in DataFrame
        df = pd.DataFrame.from_dict(weights, orient="index")
        df = df.rename_axis("Objective").reset_index()
        cols = ["Objective", "w", "v"]
        df = df[cols] if all(c in df.columns for c in cols[1:]) else df

        self.tables["OBJ_res"] = df
       
        if print_table:
            table=pt()
            table.field_names = ["Objective","Weight" ,"Value","Weighted Value"]
            for _, row in df.iterrows():
                w = row.get("w", 0.0)
                v = row.get("v", 0.0)
                table.add_row([
                    row["Objective"],
                    f"{w:.2f}",
                    f"{v:,.2f}".replace(',', ' '),
                    f"{w*v:,.2f}".replace(',', ' '),
                ])
            print(table)

        return df
        
    def TEP_TS_norm(self, print_table=True):
        if not self.Grid.OPF_obj['PZ_cost_of_generation']['w'] > 0:
            return None
        tot = 0
        tot_n = 0

        for l in self.Grid.lines_AC_exp:
            if l.np_line_opf:
                
                opt=l.np_line
                cost=((opt)*l.MVA_rating*l.Length_km*l.phi)*l.life_time*8760/(10**6)
                tot+=cost
                tot_n+=((opt)*l.MVA_rating*l.Length_km*l.phi)/1000

        for l in self.Grid.lines_DC:
            if l.np_line_opf:
                opt=l.np_line
                cost=((opt)*l.MW_rating*l.Length_km*l.phi)*l.life_time*8760/(10**6)
                tot+=cost
                tot_n+=((opt)*l.MW_rating*l.Length_km*l.phi)/1000
                
        
        for cn in self.Grid.Converters_ACDC:
            if cn.np_conv_opf:
                opt=cn.np_conv
                cost=((opt)*cn.MVA_max*cn.phi)*cn.life_time*8760/(10**6)
                tot+=cost
                tot_n+=((opt)*cn.MVA_max*cn.phi)/1000
        
        TEP_multiScenario_res = self.Grid.TEP_multiScenario_res
        SC = TEP_multiScenario_res['PZ_cost_of_generation']
        weight = TEP_multiScenario_res['weights']
        price = TEP_multiScenario_res['price']
        OPF_obj = TEP_multiScenario_res['OPF_obj']
       
        # Per-price-zone normalized costs
        rows_zones = []
        n_years = self.Grid.TEP_n_years
        discount_rate = self.Grid.TEP_discount_rate
        
        
        for m in self.Grid.Price_Zones:
            if type(m) is Price_Zone:
                price_zone_weighted = SC.loc[m.name]
                weighted_total = price_zone_weighted * weight.loc['Weight']
                weighted_total = weighted_total.sum()
                weighted_price = price.loc[m.name]* weight.loc['Weight']
                weighted_price = weighted_price.sum()
                present_value=0
                for year in range(1, n_years + 1):
                    # Discount each yearly cash flow and add to the present value
                    present_value += (weighted_total * 8760) / ((1 + discount_rate) ** year)/1000
                
                rows_zones.append([m.name, weighted_total, weighted_price, present_value])

        df_zones = pd.DataFrame(rows_zones, columns=[
            "Price_Zone", "Normalized Cost Generation[k€/h]", "Average price [€/MWh]","Present Value Cost Gen [M€]"
        ])
        self.tables["TEP_TS_norm_zones"] = df_zones

        # Normalized investment summary
        weighted_sum = SC.loc['Weighted SC'].sum()
        df_norm = pd.DataFrame([[weighted_sum, tot_n, weighted_sum+tot_n]], columns=[
            "Normalized Cost Generation[k€/h]","Normalized investment [k€/h]","Normalized Total cost [k€/h]"
        ])
        self.tables["TEP_TS_norm_summary"] = df_norm

        # NPV summary
        tot_pv=0
        for year in range(1, n_years + 1):
            # Discount each yearly cash flow and add to the present value
            tot_pv += (weighted_sum * 8760) / ((1 + discount_rate) ** year)/1000
        df_npv = pd.DataFrame([[tot_pv, tot, -(tot_pv + tot)]], columns=[
            "Present Value Cost Generation[M€]","Investment [M€]","NPV [M€]"
        ])
        self.tables["TEP_TS_norm_NPV"] = df_npv

        if print_table:
            # Zones table
            table=pt()
            table.field_names = ["Price_Zone", "Normalized Cost Generation[k€/h]", "Average price [€/MWh]","Present Value Cost Gen [M€]"]
            for _, row in df_zones.iterrows():
                table.add_row([
                    row["Price_Zone"],
                    np.round(row["Normalized Cost Generation[k€/h]"], decimals=2),
                    np.round(row["Average price [€/MWh]"], decimals=2),
                    np.round(row["Present Value Cost Gen [M€]"], decimals=2),
                ])
            print(table)
            
            # Normalized summary
            table=pt()
            table.field_names = ["Normalized Cost Generation[k€/h]","Normalized investment [k€/h]","Normalized Total cost [k€/h]"]
            w_sum, t_n, t_tot = df_norm.iloc[0]
            table.add_row([
                np.round(w_sum, decimals=2),
                np.round(t_n, decimals=2),
                np.round(t_tot, decimals=2),
            ])
            print(table)
            
            # NPV summary
            table=pt()
            table.field_names = ["Present Value Cost Generation[M€]","Investment [M€]","NPV [M€]"]
            pv, inv, npv = df_npv.iloc[0]
            table.add_row([
                f"{np.round(pv, decimals=2):,}".replace(',', ' '),
                f"{np.round(inv, decimals=2):,}".replace(',', ' '),
                f"{-np.round(npv, decimals=2):,}".replace(',', ' '),
            ])  
            print(table)

        return {
            "zones": df_zones,
            "summary": df_norm,
            "NPV": df_npv,
        }

    def MP_TEP_results(self, print_table=True):
        # Check if the attribute exists and is a DataFrame
        if hasattr(self.Grid, "MP_TEP_results") and isinstance(self.Grid.MP_TEP_results, pd.DataFrame):
            df = self.Grid.MP_TEP_results
            self.tables["MP_TEP_results_raw"] = df

            # Build metric-wise tables (similar style to MP_TEP_fuel_type_distribution)
            y = getattr(self.Grid, "TEP_n_years", 1)

            def _period_label(period):
                p_int = int(period)
                return f"Inv year {int((p_int - 1) * y)}"

            period_ids = []
            for col in df.columns:
                for prefix in ("Installed_", "Decommissioned_", "Active_", "Cost_"):
                    if col.startswith(prefix):
                        suffix = col[len(prefix):]
                        if suffix.isdigit():
                            period_ids.append(int(suffix))
            period_ids = sorted(set(period_ids))

            metric_tables = {}

            metric_prefix = {
                "Installed": "Installed_",
                "Decommissioned": "Decommissioned_",
                "Active": "Active_",
                "Cost": "Cost_",
            }

            for metric_name, prefix in metric_prefix.items():
                cols = [c for c in ("Element", "Type") if c in df.columns]
                if metric_name == "Active" and "Pre Existing" in df.columns:
                    cols.append("Pre Existing")
                metric_df = df[cols].copy()
                for p in period_ids:
                    src_col = f"{prefix}{p}"
                    out_col = _period_label(p)
                    metric_df[out_col] = df[src_col] if src_col in df.columns else np.nan
                if metric_name == "Cost" and "Total_Cost" in df.columns:
                    metric_df["Total_Cost"] = df["Total_Cost"]
                metric_tables[metric_name] = metric_df

            # Stacked export table (one metric section under another), similar to
            # MP_TEP_fuel_type_distribution for easier Excel reading.
            stacked_blocks = []
            for metric_name in ["Installed", "Decommissioned", "Active", "Cost"]:
                if metric_name not in metric_tables:
                    continue
                section_df = metric_tables[metric_name].copy()
                value_cols = [c for c in section_df.columns if c not in ("Element", "Type")]
                title_row = {"Variable": metric_name, "Element": "", "Type": ""}
                title_row.update({c: "" for c in value_cols})
                section_df.insert(0, "Variable", "")
                spacer_row = {"Variable": "", "Element": "", "Type": ""}
                spacer_row.update({c: "" for c in value_cols})
                stacked_blocks.extend([
                    pd.DataFrame([title_row]),
                    section_df,
                    pd.DataFrame([spacer_row]),
                ])
            stacked_df = pd.concat(stacked_blocks, ignore_index=True) if stacked_blocks else pd.DataFrame()
            self.tables["MP_TEP_results"] = stacked_df

            for name, tbl in metric_tables.items():
                key = f"MP_TEP_results_{name.lower().replace(' ', '_')}"
                self.tables[key] = tbl

            if print_table:
                print('--------------')
                print('Dynamic Transmission Expansion Problem')
                print('')
                print('Investments in elements')
                print('')
                for metric_name in ["Installed", "Decommissioned", "Active", "Cost"]:
                    if metric_name not in metric_tables:
                        continue
                    df_metric = metric_tables[metric_name]
                    print(metric_name)
                    table = pt()
                    table.field_names = list(df_metric.columns)
                    for row in df_metric.itertuples(index=False):
                        row_list = list(row)
                        formatted_row = []
                        for val in row_list:
                            if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                                formatted_row.append(' ')
                            elif isinstance(val, (int, float)):
                                rounded_val = int(round(val))
                                formatted_row.append(f"{rounded_val:,}".replace(',', ' '))
                            else:
                                formatted_row.append(val)
                        table.add_row(formatted_row)
                    print(table)
                    print('')
                print('')

            return df
        else:
            if print_table:
                print(self.Grid.MP_TEP_results)
            return self.Grid.MP_TEP_results

    def MP_MS_TEP_results(self, print_table=True):
        data = getattr(self.Grid, "MP_MS_TEP_results", None)
        if not isinstance(data, dict):
            if print_table:
                print("No MP_MS_TEP_results found")
            return data

        period_results = data.get("period_results")
        objective_summary = data.get("objective_summary")
        investment_summary = data.get("investment_summary")

        if isinstance(objective_summary, pd.DataFrame):
            self.tables["MP_MS_TEP_results_objective_summary"] = objective_summary
        if isinstance(investment_summary, pd.DataFrame):
            self.tables["MP_MS_TEP_results_investment_summary"] = investment_summary

        meta_df = pd.DataFrame([{
            "n_clusters": data.get("n_clusters"),
            "n_period_results": len(period_results) if isinstance(period_results, list) else np.nan,
            "has_period_scenario_grid_res": isinstance(data.get("period_scenario_grid_res"), dict),
        }])
        self.tables["MP_MS_TEP_results_meta"] = meta_df

        if print_table:
            print('--------------')
            print('Dynamic Transmission Expansion Problem (MP+MS)')
            print('')
            print('Stored run summary')
            print('')
            table = pt()
            table.field_names = ["Item", "Value"]
            table.add_row(["n_clusters", data.get("n_clusters")])
            table.add_row(["period_results", len(period_results) if isinstance(period_results, list) else "n/a"])
            table.add_row(["period_scenario_grid_res", "yes" if isinstance(data.get("period_scenario_grid_res"), dict) else "no"])
            table.add_row(["objective_summary_df", "yes" if isinstance(objective_summary, pd.DataFrame) else "no"])
            table.add_row(["investment_summary_df", "yes" if isinstance(investment_summary, pd.DataFrame) else "no"])
            print(table)
            print('')

        return data

    def MP_TEP_obj_res(self, print_table=True):
        df = self.Grid.MP_TEP_obj_res
        self.tables["MP_TEP_obj_res"] = df

        if print_table:
            print('')
            print('Dynamic Transmission Expansion Problem')
            print('')
            print('Objective results:')
            print('')
            table = pt()
            # Exclude NPV_STEP_Objective from the display
            columns_to_show = ["Investment_Period", "OPF_Objective","NPV_OPF_Objective","TEP_Objective","STEP_Objective"]
            # Custom column names for display
            display_names = ["Investment Period", "Operational Cost [€]", "NPV Operational Cost [€]", "Investment Cost [€]", "Total STEP Cost [€]"]
            table.field_names = display_names
            for _, row in df.iterrows():
                formatted_row = []
                for col in columns_to_show:
                    val = row[col]
                    if isinstance(val, (int,float)):
                        if isinstance(val, int):
                            rounded_val = val
                        else:
                            rounded_val = np.round(val, decimals=self.dec)
                        # Format with thousand separators (spaces) and decimal places
                        formatted_val = f"{rounded_val:,.{self.dec}f}".replace(',', ' ')
                        formatted_row.append(formatted_val)
                    else:
                        formatted_row.append(val)
                table.add_row(formatted_row)
            print(table)

            table2=pt()
            table2.field_names = ["Investment_Period", "NPV Cost"]
            tot_npv_cost=0
            for _, row in df.iterrows():
                inv = row['Investment_Period']
                npv_cost = row['NPV_STEP_Objective']
                # Format numeric values with thousand separators (spaces) and decimal places
                if isinstance(npv_cost, (int, float)):
                    rounded_val = np.round(npv_cost, decimals=self.dec)
                    formatted_npv_cost = f"{rounded_val:,.{self.dec}f}".replace(',', ' ')
                else:
                    formatted_npv_cost = npv_cost
                table2.add_row([inv, formatted_npv_cost])
                tot_npv_cost+=npv_cost
            table2.add_row(['',''])    
            # Format total with thousand separators (spaces) and decimal places
            formatted_total = f"{np.round(tot_npv_cost, decimals=self.dec):,.{self.dec}f}".replace(',', ' ')
            table2.add_row(['Total', formatted_total])
            print(table2)
            print('')

        return df

    def MP_MS_TEP_obj_res(self, print_table=True):
        df = getattr(self.Grid, "MP_MS_TEP_obj_res", None)
        if df is None:
            if print_table:
                print("No MP_MS_TEP_obj_res found")
            return df

        self.tables["MP_MS_TEP_obj_res"] = df

        if print_table:
            print('')
            print('Dynamic Transmission Expansion Problem (MP+MS)')
            print('')
            print('Objective results:')
            print('')
            table = pt()
            preferred_columns = [
                ("Investment_Period", "Investment Period"),
                ("OPEX_Objective", "Operational Cost [€]"),
                ("TEP_Objective", "Investment Cost [€]"),
                ("STEP_Objective", "Total STEP Cost [€]"),
                ("STEP_Objective_Economic", "Total STEP Cost (Economic) [€]"),
            ]
            columns_to_show = [c for c, _ in preferred_columns if c in df.columns]
            display_names = [d for c, d in preferred_columns if c in df.columns]

            if columns_to_show:
                table.field_names = display_names
                for _, row in df.iterrows():
                    formatted_row = []
                    for col in columns_to_show:
                        val = row[col]
                        if isinstance(val, (int, float)):
                            rounded_val = val if isinstance(val, int) else np.round(val, decimals=self.dec)
                            formatted_row.append(f"{rounded_val:,.{self.dec}f}".replace(',', ' '))
                        else:
                            formatted_row.append(val)
                    table.add_row(formatted_row)
                print(table)
            else:
                print(df)

            if "NPV_STEP_Objective" in df.columns:
                table2 = pt()
                table2.field_names = ["Investment_Period", "NPV Cost"]
                tot_npv_cost = 0
                for _, row in df.iterrows():
                    inv = row["Investment_Period"] if "Investment_Period" in df.columns else ""
                    npv_cost = row["NPV_STEP_Objective"]
                    if isinstance(npv_cost, (int, float)):
                        rounded_val = np.round(npv_cost, decimals=self.dec)
                        formatted_npv_cost = f"{rounded_val:,.{self.dec}f}".replace(',', ' ')
                    else:
                        formatted_npv_cost = npv_cost
                    table2.add_row([inv, formatted_npv_cost])
                    if isinstance(npv_cost, (int, float)):
                        tot_npv_cost += npv_cost
                table2.add_row(['', ''])
                formatted_total = f"{np.round(tot_npv_cost, decimals=self.dec):,.{self.dec}f}".replace(',', ' ')
                table2.add_row(['Total', formatted_total])
                print(table2)
            print('')
        return df

    def MP_TEP_fuel_type_distribution(self, print_table=True):
        dist = getattr(self.Grid, "MP_TEP_fuel_type_distribution", None)

        if not isinstance(dist, dict):
            if print_table:
                print("No MP_TEP_fuel_type_distribution found")
            return dist

        self.MP_TEP_fuel_type_distribution_dict = dist

        periods = sorted(int(p) for p in dist.keys())

        y = self.Grid.TEP_n_years

        def _period_label(period):
            p_int = int(period)
            if p_int == 0:
                return "pre existing"
            return f"Inv year {int((p_int - 1) * y)}"

        period_cols = [_period_label(p) for p in periods]
        metrics = [
            "number of gen",
            "total install cap",
            "percentage",
            "current limit"
        ]

        normalized_metric_by_period = {m: {} for m in metrics}
        all_types = set()

        for period in periods:
            df = dist[period]
            if not isinstance(df, pd.DataFrame) or "Type" not in df.columns:
                continue
            tmp = df.copy()
            for col in metrics:
                if col not in tmp.columns:
                    tmp[col] = np.nan
            tmp = tmp[["Type"] + metrics]
            all_types.update(tmp["Type"].dropna().astype(str).tolist())
            for metric in metrics:
                normalized_metric_by_period[metric][period] = tmp[["Type", metric]].copy()

        type_order = [t for t in sorted(all_types) if t not in ("All", "System load (all nodes)")]
        if "All" in all_types:
            type_order.append("All")
        if "System load (all nodes)" in all_types:
            type_order.append("System load (all nodes)")

        metric_tables = {}
        s_base = self.Grid.S_base
        for metric in metrics:
            metric_df = pd.DataFrame({"Type": type_order})
            for period in periods:
                col_name = _period_label(period)
                if period not in normalized_metric_by_period[metric]:
                    metric_df[col_name] = np.nan
                    continue
                tmp = normalized_metric_by_period[metric][period].rename(columns={metric: col_name})
                metric_df = metric_df.merge(tmp, on="Type", how="left")
            if metric == "total install cap":
                for col_name in period_cols:
                    if col_name in metric_df.columns:
                        metric_df[col_name] = pd.to_numeric(metric_df[col_name], errors="coerce") * s_base
            metric_tables[metric] = metric_df

        self.tables["MP_TEP_fuel_type_distribution_number_of_gen"] = metric_tables["number of gen"]
        self.tables["MP_TEP_fuel_type_distribution_total_install_cap"] = metric_tables["total install cap"]
        self.tables["MP_TEP_fuel_type_distribution_percentage"] = metric_tables["percentage"]
        self.tables["MP_TEP_fuel_type_distribution_current_limit"] = metric_tables["current limit"] 

        # Stacked export table (one metric section under another)
        stacked_blocks = []
        for metric in metrics:
            metric_title = "total install cap (MW)" if metric == "total install cap" else metric
            section_title = pd.DataFrame([{"Variable": metric_title, "Type": "", **{c: "" for c in period_cols}}])
            section_data = metric_tables[metric].copy()
            section_data.insert(0, "Variable", "")
            section_spacer = pd.DataFrame([{"Variable": "", "Type": "", **{c: "" for c in period_cols}}])
            stacked_blocks.extend([section_title, section_data, section_spacer])
        stacked_df = pd.concat(stacked_blocks, ignore_index=True) if stacked_blocks else pd.DataFrame()
        self.tables["MP_TEP_fuel_type_distribution"] = stacked_df

        if print_table:
            print('--------------')
            print('Dynamic Transmission Expansion Problem')
            print('')
            print('Fuel type distribution by investment period')
            print('')

            for metric in metrics:
                df_metric = metric_tables[metric]
                metric_title = "total install cap (MW)" if metric == "total install cap" else metric
                print(metric_title)
                table = pt()
                table.field_names = list(df_metric.columns)
                for row in df_metric.itertuples(index=False):
                    row_list = list(row)
                    formatted_row = []
                    for col_name, val in zip(df_metric.columns, row_list):
                        if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                            formatted_row.append(' ')
                        elif isinstance(val, (int, float)):
                            if metric == "percentage":
                                formatted_row.append(f"{val:,.{self.dec}f}".replace(',', ' '))
                            else:
                                rounded_val = int(round(val))
                                formatted_row.append(f"{rounded_val:,}".replace(',', ' '))
                        else:
                            formatted_row.append(val)
                    table.add_row(formatted_row)
                print(table)
                print('')
            print('')

        return stacked_df

    def _render_seq_step_with_mp_renderer(
        self,
        *,
        seq_attr,
        mp_attr,
        mp_method,
        mp_table_prefix,
        seq_table_prefix,
        print_table=True,
    ):
        seq_payload = getattr(self.Grid, seq_attr, None)
        if seq_payload is None:
            return None

        had_mp_attr = hasattr(self.Grid, mp_attr)
        previous_mp_payload = getattr(self.Grid, mp_attr, None) if had_mp_attr else None
        tables_before = set(self.tables.keys())
        setattr(self.Grid, mp_attr, seq_payload)

        try:
            out = mp_method(print_table=print_table)
        finally:
            if had_mp_attr:
                setattr(self.Grid, mp_attr, previous_mp_payload)
            else:
                delattr(self.Grid, mp_attr)

        new_mp_keys = [
            key for key in list(self.tables.keys())
            if key.startswith(mp_table_prefix) and key not in tables_before
        ]
        for key in new_mp_keys:
            mapped_key = f"{seq_table_prefix}{key[len(mp_table_prefix):]}"
            self.tables[mapped_key] = self.tables[key]
            del self.tables[key]

        return out

    def Seq_STEP_results(self, print_table=True):
        df = getattr(self.Grid, "Seq_STEP_results", None)
        if df is None:
            if print_table:
                print("No Seq_STEP_results found")
            return df
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_STEP_results",
            mp_attr="MP_TEP_results",
            mp_method=self.MP_TEP_results,
            mp_table_prefix="MP_TEP_results",
            seq_table_prefix="Seq_STEP_results",
            print_table=print_table,
        )

    def Seq_STEP_obj_res(self, print_table=True):
        df = getattr(self.Grid, "Seq_STEP_obj_res", None)
        if df is None:
            if print_table:
                print("No Seq_STEP_obj_res found")
            return df
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_STEP_obj_res",
            mp_attr="MP_TEP_obj_res",
            mp_method=self.MP_TEP_obj_res,
            mp_table_prefix="MP_TEP_obj_res",
            seq_table_prefix="Seq_STEP_obj_res",
            print_table=print_table,
        )

    def Seq_STEP_fuel_type_distribution(self, print_table=True):
        dist = getattr(self.Grid, "Seq_STEP_fuel_type_distribution", None)
        if dist is None:
            if print_table:
                print("No Seq_STEP_fuel_type_distribution found")
            return dist
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_STEP_fuel_type_distribution",
            mp_attr="MP_TEP_fuel_type_distribution",
            mp_method=self.MP_TEP_fuel_type_distribution,
            mp_table_prefix="MP_TEP_fuel_type_distribution",
            seq_table_prefix="Seq_STEP_fuel_type_distribution",
            print_table=print_table,
        )

    def Seq_MS_STEP_results(self, print_table=True):
        df = getattr(self.Grid, "Seq_MS_STEP_results", None)
        if df is None:
            if print_table:
                print("No Seq_MS_STEP_results found")
            return df
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_MS_STEP_results",
            mp_attr="MP_TEP_results",
            mp_method=self.MP_TEP_results,
            mp_table_prefix="MP_TEP_results",
            seq_table_prefix="Seq_MS_STEP_results",
            print_table=print_table,
        )

    def Seq_MS_STEP_obj_res(self, print_table=True):
        df = getattr(self.Grid, "Seq_MS_STEP_obj_res", None)
        if df is None:
            if print_table:
                print("No Seq_MS_STEP_obj_res found")
            return df
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_MS_STEP_obj_res",
            mp_attr="MP_TEP_obj_res",
            mp_method=self.MP_TEP_obj_res,
            mp_table_prefix="MP_TEP_obj_res",
            seq_table_prefix="Seq_MS_STEP_obj_res",
            print_table=print_table,
        )

    def Seq_MS_STEP_fuel_type_distribution(self, print_table=True):
        dist = getattr(self.Grid, "Seq_MS_STEP_fuel_type_distribution", None)
        if dist is None:
            if print_table:
                print("No Seq_MS_STEP_fuel_type_distribution found")
            return dist
        return self._render_seq_step_with_mp_renderer(
            seq_attr="Seq_MS_STEP_fuel_type_distribution",
            mp_attr="MP_TEP_fuel_type_distribution",
            mp_method=self.MP_TEP_fuel_type_distribution,
            mp_table_prefix="MP_TEP_fuel_type_distribution",
            seq_table_prefix="Seq_MS_STEP_fuel_type_distribution",
            print_table=print_table,
        )

    def Price_Zone(self, print_table=True):
        rows = []
        
        tot_sc=0
        tot_Rgen_cost=0
        tot_gen_cost=0
        tot_curt_cost=0
        tot_m_tot=0
        
        for m in self.Grid.Price_Zones:
            
            Rgen = sum(rs.PGi_ren * rs.gamma for node in m.nodes_AC for rs in node.connected_RenSource) * self.Grid.S_base
            
            gen = sum(node.PGi+node.PGi_opt for node in m.nodes_AC)*self.Grid.S_base
            load = sum(node.PLi for node in m.nodes_AC)*self.Grid.S_base
            ie = Rgen+gen-load
            price=m.price
            
            sc = (m.a*ie**2+ie*m.b)/1000
            if not self.Grid.OnlyGen or self.Grid.OPF_Price_Zones_constraints_used:
                Rgen_cost=Rgen*m.price/1000
            else:
                Rgen_cost= 0          
            gen_cost = gen*m.price/1000
            if self.Grid.CurtCost==False:
                curt_cost=0
            else:  
                curt_cost= sum((rs.PGi_ren-rs.PGi_ren * rs.gamma)*rs.sigma*node.price for node in m.nodes_AC for rs in node.connected_RenSource)*self.Grid.S_base
            m_tot= Rgen_cost+gen_cost+curt_cost+sc
            
            tot_sc+=sc
            tot_Rgen_cost+=Rgen_cost
            tot_gen_cost+=gen_cost
            tot_curt_cost+=curt_cost
            tot_m_tot+=m_tot
            
            if ie >=0:
                export = ie
                imp = 0
            else: 
                export = 0
                imp = abs(ie)
            rows.append({
                "Price_Zone": m.name,
                "Renewable Generation(MW)": np.round(Rgen, decimals=self.dec),
                "Generation (MW)": np.round(gen, decimals=self.dec),
                "Load (MW)": np.round(load, decimals=self.dec),
                "Import (MW)": np.round(imp, decimals=self.dec),
                "Export (MW)": np.round(export, decimals=self.dec),
                "Price (€/MWh)": np.round(price, decimals=2),
                "Social Cost [k€]": np.round(sc, decimals=self.dec),
                "Renewable Gen Cost [k€]": np.round(Rgen_cost, decimals=self.dec),
                "Curtailment Cost [k€]": np.round(curt_cost, decimals=self.dec),
                "Generation Cost [k€]": np.round(gen_cost, decimals=self.dec),
                "Total Cost [k€]": np.round(m_tot, decimals=self.dec),
            })
        
        if rows:
            rows.append({
                "Price_Zone": "Total",
                "Renewable Generation(MW)": "",
                "Generation (MW)": "",
                "Load (MW)": "",
                "Import (MW)": "",
                "Export (MW)": "",
                "Price (€/MWh)": "",
                "Social Cost [k€]": np.round(tot_sc, decimals=self.dec),
                "Renewable Gen Cost [k€]": np.round(tot_Rgen_cost, decimals=self.dec),
                "Curtailment Cost [k€]": np.round(tot_curt_cost, decimals=self.dec),
                "Generation Cost [k€]": np.round(tot_gen_cost, decimals=self.dec),
                "Total Cost [k€]": np.round(tot_m_tot, decimals=self.dec),
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=[
                "Price_Zone","Renewable Generation(MW)","Generation (MW)", "Load (MW)",
                "Import (MW)","Export (MW)","Price (€/MWh)",
                "Social Cost [k€]","Renewable Gen Cost [k€]","Curtailment Cost [k€]",
                "Generation Cost [k€]","Total Cost [k€]"
            ]
        )
        self.tables["Price_Zone"] = df
        
        if print_table and not df.empty:
            print('--------------')
            print('Price_Zone')
            # First table: energy balance & price
            table = pt()
            table.field_names = ["Price_Zone","Renewable Generation(MW)" ,"Generation (MW)", "Load (MW)","Import (MW)","Export (MW)","Price (€/MWh)"]
            for _, row in df.iterrows():
                if row["Price_Zone"] == "Total":
                    continue
                table.add_row([
                    row["Price_Zone"],
                    row["Renewable Generation(MW)"],
                    row["Generation (MW)"],
                    row["Load (MW)"],
                    row["Import (MW)"],
                    row["Export (MW)"],
                    row["Price (€/MWh)"],
                ])
            # Second table: cost breakdown
            table2 = pt()
            table2.field_names = ["Price_Zone","Social Cost [k€]","Renewable Gen Cost [k€]","Curtailment Cost [k€]","Generation Cost [k€]","Total Cost [k€]"]
            for _, row in df.iterrows():
                table2.add_row([
                    row["Price_Zone"],
                    row["Social Cost [k€]"],
                    row["Renewable Gen Cost [k€]"],
                    row["Curtailment Cost [k€]"],
                    row["Generation Cost [k€]"],
                    row["Total Cost [k€]"],
                ])
            print(table)
            print(table2)
            
        return df
    def DC_lines_current(self, print_table=True):
        
        rows = []
        base = self.Grid.S_base

        for g in range(self.Grid.Num_Grids_DC):
            for line in self.Grid.lines_DC:
                if line.np_line < 0.01:
                    continue
                if self.Grid.Graph_line_to_Grid_index_DC[line] != g:
                    continue
                i = line.fromNode.nodeNumber
                j = line.toNode.nodeNumber
                I_base = base/line.kV_base
                i_to = self.Grid.Iij_DC[j, i]*I_base
                i_from = self.Grid.Iij_DC[i, j]*I_base
                line_current = max(abs(i_to), abs(i_from))

                p_to = line.toP*base/line.np_line
                p_from = line.fromP*base/line.np_line

                load = max(p_to, p_from)/line.MW_rating*100

                if line.m_sm_b == 'm':
                    pol = "Monopolar (asymmetrically grounded)"
                elif line.m_sm_b == 'sm':
                    pol = "Monopolar (symmetrically grounded)"
                elif line.m_sm_b == 'b':
                    pol = "Bipolar"
                else:
                    pol = ""

                rows.append({
                    "Line": line.name,
                    "From bus": line.fromNode.name,
                    "To bus": line.toNode.name,
                    "I (kA)": np.round(line_current, decimals=self.dec),
                    "Loading %": np.round(load, decimals=self.dec),
                    "Capacity [kA]": np.round(line.MW_rating*line.np_line/(line.kV_base*line.pol), decimals=self.dec),
                    "Polarity": pol,
                    "Grid": g+1
                })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Line", "From bus", "To bus", "I (kA)", "Loading %", "Capacity [kA]", "Polarity", "Grid"]
        )

        self.tables["DC_lines_current"] = df_all

        if print_table:
            print('--------------')
            print('Results DC Lines current')
            for g in range(self.Grid.Num_Grids_DC):
                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue
                print(f'Grid DC {g+1}')
                tablei = pt()
                tablei.field_names = ["Line", "From bus", "To bus", "I (kA)", "Loading %", "Capacity [kA]", "Polarity"]
                tablei.align["Polarity"] = 'l'
                for _, row in df_grid.iterrows():
                    tablei.add_row([
                        row["Line"],
                        row["From bus"],
                        row["To bus"],
                        row["I (kA)"],
                        row["Loading %"],
                        row["Capacity [kA]"],
                        row["Polarity"],
                    ])
                print(tablei)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/DC_line_current.csv'
            df_all.to_csv(csv_filename, index=False)
                
        return df_all

    def DC_lines_power(self, print_table=True):
        
        rows = []
        base = self.Grid.S_base

        for g in range(self.Grid.Num_Grids_DC):
            for line in self.Grid.lines_DC:
                if line.np_line <= 0.01:
                    continue
                if self.Grid.Graph_line_to_Grid_index_DC[line] != g:
                    continue
                p_to = line.toP*base
                p_from = line.fromP*base
                Ploss = np.real(line.loss)*base

                rows.append({
                    "Line": line.name,
                    "From bus": line.fromNode.name,
                    "To bus": line.toNode.name,
                    "P from (MW)": np.round(p_from, decimals=self.dec),
                    "P to (MW)": np.round(p_to, decimals=self.dec),
                    "Power loss (MW)": np.round(Ploss, decimals=self.dec),
                    "Capacity [MW]": int(line.MW_rating*line.np_line),
                    "Grid": g+1
                })

        df_all = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Line", "From bus", "To bus", "P from (MW)", "P to (MW)", "Power loss (MW)", "Capacity [MW]", "Grid"]
        )

        self.tables["DC_lines_power"] = df_all

        if print_table:
            print('--------------')
            print('Results DC Lines power')
            for g in range(self.Grid.Num_Grids_DC):
                df_grid = df_all[df_all["Grid"] == (g+1)]
                if df_grid.empty:
                    continue
                print(f'Grid DC {g+1}')
                tablep = pt()
                tablep.field_names = ["Line", "From bus", "To bus", "P from (MW)", "P to (MW)", "Power loss (MW)", "Capacity [MW]"]
                for _, row in df_grid.iterrows():
                    tablep.add_row([
                        row["Line"],
                        row["From bus"],
                        row["To bus"],
                        row["P from (MW)"],
                        row["P to (MW)"],
                        row["Power loss (MW)"],
                        row["Capacity [MW]"],
                    ])
                print(tablep)

        if self.save_res and self.export_type == "csv":
            csv_filename = f'{self.export_location}/DC_line_power.csv'
            df_all.to_csv(csv_filename, index=False)

        return df_all

    def DC_converter(self, print_table=True):
        rows = []
        base = self.Grid.S_base

        for conv in self.Grid.Converters_DCDC:
            fromMW = conv.Powerfrom*base
            toMW = conv.Powerto*base
            loss = np.abs(fromMW+toMW)
            rows.append({
                "Converter": conv.name,
                "From node": conv.fromNode.name,
                "To node": conv.toNode.name,
                "Power from (MW)": np.round(fromMW, decimals=self.dec),
                "Power To (MW)": np.round(toMW, decimals=self.dec),
                "Power Loss (MW)": np.round(loss, decimals=self.dec),
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Converter", "From node", "To node", "Power from (MW)", "Power To (MW)", "Power Loss (MW)"]
        )
        self.tables["DC_converter"] = df

        if print_table:
            print('-----------')
            print('DC DC Coverters')
            table = pt()
            table.field_names = ["Converter", "From node", "To node",
                                 "Power from (MW)", "Power To (MW)", "Power Loss (MW)"]
            for _, row in df.iterrows():
                table.add_row([
                    row["Converter"],
                    row["From node"],
                    row["To node"],
                    row["Power from (MW)"],
                    row["Power To (MW)"],
                    row["Power Loss (MW)"],
                ])
            print(table)

        return df

    def Converter(self, print_table=True):
        rows_main = []
        rows_cap = []
        base = self.Grid.S_base

        for conv in self.Grid.Converters_ACDC:
            if conv.np_conv <= 0.01:
                continue
            P_DC = np.round(conv.P_DC*base, decimals=self.dec)
            P_s = np.round(conv.P_AC*base, decimals=self.dec)
            Q_s = np.round(conv.Q_AC*base, decimals=self.dec)
            P_c = np.round(conv.Pc*base, decimals=self.dec)
            Q_c = np.round(conv.Qc*base, decimals=self.dec)
            P_loss = np.round(conv.P_loss*base, decimals=self.dec)
            Ploss_tf = np.round(conv.P_loss_tf*base, decimals=self.dec)
            loading = np.round(conv.loading, decimals=self.dec)

            rows_main.append({
                "Converter": conv.name,
                "AC node": conv.Node_AC.name,
                "DC node": conv.Node_DC.name,
                "Power s AC (MW)": P_s,
                "Reactive s AC (MVAR)": Q_s,
                "Power c AC (MW)": P_c,
                "Power DC(MW)": P_DC,
                "Reactive power (MVAR)": Q_c,
                "Power loss IGBTs (MW)": P_loss,
                "Power loss AC elements (MW)": Ploss_tf,
            })
            rows_cap.append({
                "Converter": conv.name,
                "AC control mode": conv.AC_type,
                "DC control mode": conv.type,
                "Loading %": loading,
                "Capacity [MVA]": int(conv.MVA_max*conv.np_conv),
            })

        df_main = pd.DataFrame(rows_main) if rows_main else pd.DataFrame(
            columns=[
                "Converter", "AC node", "DC node", "Power s AC (MW)",
                "Reactive s AC (MVAR)", "Power c AC (MW)", "Power DC(MW)",
                "Reactive power (MVAR)", "Power loss IGBTs (MW)", "Power loss AC elements (MW)"
            ]
        )
        df_cap = pd.DataFrame(rows_cap) if rows_cap else pd.DataFrame(
            columns=["Converter", "AC control mode", "DC control mode", "Loading %", "Capacity [MVA]"]
        )

        # Combined DataFrame used for return value and Excel export
        if not df_main.empty:
            df_combined = pd.merge(df_main, df_cap, on="Converter", how="left")
        else:
            df_combined = df_main.copy()

        self.tables["Converter"] = df_combined

        if print_table and not df_main.empty:
            print('------------')
            print('AC DC Converters')
            table = pt()
            table2 = pt()
            table.field_names = ["Converter", "AC node", "DC node","Power s AC (MW)","Reactive s AC (MVAR)", "Power c AC (MW)", "Power DC(MW)", "Reactive power (MVAR)", "Power loss IGBTs (MW)", "Power loss AC elements (MW)"]
            table2.field_names = ["Converter","AC control mode", "DC control mode","Loading %","Capacity [MVA]"]
            for _, row in df_main.iterrows():
                table.add_row([
                    row["Converter"],
                    row["AC node"],
                    row["DC node"],
                    row["Power s AC (MW)"],
                    row["Reactive s AC (MVAR)"],
                    row["Power c AC (MW)"],
                    row["Power DC(MW)"],
                    row["Reactive power (MVAR)"],
                    row["Power loss IGBTs (MW)"],
                    row["Power loss AC elements (MW)"],
                ])
            for _, row in df_cap.iterrows():
                table2.add_row([
                    row["Converter"],
                    row["AC control mode"],
                    row["DC control mode"],
                    row["Loading %"],
                    row["Capacity [MVA]"],
                ])
            print(table)
            print(table2)

        if self.save_res and self.export_type == "csv" and not df_main.empty:
            csv_filename = f'{self.export_location}/Converter_results.csv'
            # Save full combined DataFrame (including capacity columns)
            df_combined.to_csv(csv_filename, index=False)

        return df_combined

    @staticmethod
    def _build_pyomo_model_results_df(model, solver_stats=None, model_results=None, decimals=2):
        """Build Pyomo model summary table and raw row dict."""
        try:
            import pyomo.environ as pyo
        except ImportError:
            return pd.DataFrame(), {}

        obj_scaling = getattr(model, 'obj_scaling', 1.0)

        # --- Objective value ---
        obj_value_scaled = None
        obj_value_real = None
        try:
            obj_comp = next(model.component_objects(pyo.Objective, active=True))
            obj_value_scaled = pyo.value(obj_comp)
            obj_value_real = obj_value_scaled * obj_scaling
        except (StopIteration, ValueError):
            pass

        # --- Model dimensions ---
        n_vars = sum(len(v) for v in model.component_objects(pyo.Var, active=True))
        n_constraints = sum(len(c) for c in model.component_objects(pyo.Constraint, active=True))

        # Count integer/binary variables
        n_integer = 0
        n_binary = 0
        n_continuous = 0
        for var_obj in model.component_objects(pyo.Var, active=True):
            for idx in var_obj:
                v = var_obj[idx]
                if v.domain is pyo.Binary or v.domain is pyo.Boolean:
                    n_binary += 1
                elif v.domain is pyo.Integers or v.domain is pyo.NonNegativeIntegers or v.domain is pyo.PositiveIntegers:
                    n_integer += 1
                else:
                    n_continuous += 1

        # --- Solver statistics (from solver_stats dict) ---
        solver_name = None
        solve_time = None
        termination = None
        solution_found = None
        has_callback = False
        n_feasible_solutions = 0
        solver_message = ''

        if solver_stats is not None:
            solver_name = solver_stats.get('solver', None)
            solve_time = solver_stats.get('time', None)
            termination = solver_stats.get('termination_condition', None)
            solution_found = solver_stats.get('solution_found', None)
            solver_message = solver_stats.get('solver_message', '') or ''
            feasible = solver_stats.get('feasible_solutions', [])
            has_callback = len(feasible) > 0 if feasible else False
            n_feasible_solutions = len(feasible) if feasible else 0

            # Refine termination: detect "acceptable" from IPOPT message
            if termination == 'optimal' and 'Acceptable' in solver_message:
                termination = 'acceptable'

        # --- Extra info from raw Pyomo results ---
        lower_bound = None
        upper_bound = None
        gap = None

        if model_results is not None:
            try:
                lb = getattr(model_results.problem, 'lower_bound', None)
                ub = getattr(model_results.problem, 'upper_bound', None)
                if lb is not None and np.isfinite(lb):
                    lower_bound = lb
                if ub is not None and np.isfinite(ub):
                    upper_bound = ub
                if lower_bound is not None and upper_bound is not None and upper_bound != 0:
                    gap = abs(upper_bound - lower_bound) / max(abs(upper_bound), 1e-10)
            except (AttributeError, TypeError):
                pass

            try:
                time_limit_info = getattr(model_results.solver, 'time', None)
                if time_limit_info and solve_time is None:
                    solve_time = time_limit_info
            except AttributeError:
                pass

        # --- Build row, only include fields that carry useful info ---
        row = {}
        row['Model Name'] = getattr(model, 'name', '')
        if solver_name:
            row['Solver'] = solver_name
        row['Termination'] = termination
        if solver_message:
            row['Termination Message'] = solver_message
        row['Solution Found'] = solution_found
        row['Run Status'] = 'ok' if solution_found else 'failed'

        if obj_scaling != 1.0:
            row['Objective (scaled)'] = np.round(obj_value_scaled, decimals=decimals) if obj_value_scaled is not None else None
            row['Objective (real)'] = np.round(obj_value_real, decimals=decimals) if obj_value_real is not None else None
            row['Obj Scaling'] = f'{obj_scaling:.0e}'
        else:
            row['Objective'] = np.round(obj_value_real, decimals=decimals) if obj_value_real is not None else None

        row['Solve Time (s)'] = np.round(solve_time, decimals=decimals) if solve_time is not None else None

        if lower_bound is not None:
            row['Lower Bound'] = np.round(lower_bound, decimals=decimals)
        if upper_bound is not None:
            row['Upper Bound'] = np.round(upper_bound, decimals=decimals)
        if gap is not None and np.isfinite(gap):
            row['Gap'] = np.round(gap, decimals=6)
        if has_callback:
            row['Feasible Solutions'] = n_feasible_solutions

        row['Variables'] = n_vars
        row['Continuous'] = n_continuous
        if n_integer > 0:
            row['Integer'] = n_integer
        if n_binary > 0:
            row['Binary'] = n_binary
        row['Constraints'] = n_constraints

        df = pd.DataFrame([row])
        return df, row

    def pyomo_model_results(self, model, solver_stats=None, model_results=None, print_table=True):
        """
        Extract and display solver/model information from a solved Pyomo model.

        Parameters
        ----------
        model : pyomo.ConcreteModel
            The solved Pyomo model.
        solver_stats : dict, optional
            Dictionary returned by pyomo_model_solve (contains time, termination, etc.).
        model_results : pyomo SolverResults, optional
            Raw Pyomo solver results object returned by pyomo_model_solve.
        print_table : bool
            Whether to print a PrettyTable summary.

        Returns
        -------
        df : pd.DataFrame
            Single-row DataFrame with all solver/model statistics.
        """
        try:
            import pyomo.environ as pyo
        except ImportError:
            print("Pyomo is not installed — cannot extract model results.")
            return pd.DataFrame()

        df, row = self._build_pyomo_model_results_df(
            model=model,
            solver_stats=solver_stats,
            model_results=model_results,
            decimals=self.dec,
        )
        self.tables["Pyomo_Model_Results"] = df

        if print_table:
            print('--------------')
            print('Pyomo Model Results')
            print('')
            table = pt()
            table.field_names = ['Property', 'Value']
            table.align['Property'] = 'l'
            table.align['Value'] = 'r'
            for key, val in row.items():
                table.add_row([key, val])
            print(table)

        return df