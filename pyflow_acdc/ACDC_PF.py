# -*- coding: utf-8 -*-
"""
AC/DC Power Flow calculations module.
Provides functions for AC and AC/DC power flow analysis.
"""
import numpy as np
import sys
import time
from .grid_analysis import analyse_grid

__all__ = [
    'AC_PowerFlow',
    'DC_PowerFlow',
    'ACDC_sequential',
    'Power_flow'
]



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

def Power_flow(grid,tol_lim=1e-10, maxIter=100):
    analyse_grid(grid)
    if grid.ACmode and grid.DCmode:
        t,tol,_=ACDC_sequential(grid,tol_lim, maxIter)
    elif grid.ACmode:
        t,tol=AC_PowerFlow(grid,tol_lim, maxIter)
    elif grid.DCmode:
        t,tol=DC_PowerFlow(grid,tol_lim, maxIter)
    return t,tol


def AC_PowerFlow(grid, tol_lim=1e-10, maxIter=100):
    time_1 = time.perf_counter()
    grid.reset_run_flags()
    grid.Update_PQ_AC()
    grid.create_Ybus_AC()
    grid.check_stand_alone_is_slack()
    ac_tol =load_flow_AC(grid, tol_lim, maxIter)
    grid.Update_PQ_AC()
    grid.Line_AC_calc()
    grid.Line_AC_calc_exp()
    time_2 = time.perf_counter()
    return time_2-time_1,ac_tol
    
def DC_PowerFlow(grid, tol_lim=1e-10, maxIter=100,Droop_PF=True):
    time_1 = time.perf_counter()
    grid.reset_run_flags()
    grid.Update_P_DC()
    dc_tol =load_flow_DC(grid, tol_lim, maxIter,Droop_PF)
    grid.Update_P_DC()
    grid.Line_DC_calc()
    time_2 = time.perf_counter()
    return time_2-time_1,dc_tol

def ACDC_sequential(grid, tol_lim=1e-4, maxIter=100, internal_tol = 1e-8,change_slack2Droop=False, QLimit=False,Droop_PF=True):
    time_1 = time.perf_counter()
    tolerance = 1
    grid.reset_run_flags()
    grid.iter_num_seq = 0
    
    # Initialize comprehensive tolerance tracker dictionary
    tolerance_tracker = {
        'sequential_iterations': [],
        'ac_pf_tolerances': [],
        'dc_pf_tolerances': [],
        'converter_tolerances': [],
        'converter_names': [],
        'final_sequential_tolerance': None,
        'convergence_status': {
            'ac_pf_converged': True,
            'dc_pf_converged': True,
            'converters_converged': True,
            'sequential_converged': True
        }
    }
    
    for conv in grid.Converters_ACDC:
        if conv.type!= 'PAC':
            AC_node = conv.Node_AC
            DC_node = conv.Node_DC
            DC_node.Pconv = conv.P_DC
            P_DC = conv.P_DC
            conv.P_AC = -P_DC
            AC_node.P_s = conv.P_AC
            s = 1
            
    grid.Update_PQ_AC()
    grid.create_Ybus_AC()
    grid.check_stand_alone_is_slack()
    # Initialize ps_iterations as a numpy array with shape (maxIter, nn_AC)
    ps_iterations = np.zeros((maxIter, grid.nn_AC))
    
    while tolerance > tol_lim and grid.iter_num_seq < maxIter:
        grid.Ps_AC_new = np.zeros((grid.nn_AC, 1))
        
        # Track AC power flow tolerance
        ac_tol = load_flow_AC(grid, tol_lim=internal_tol)
        tolerance_tracker['ac_pf_tolerances'].append(ac_tol)
        
        for conv in grid.Converters_ACDC:
            if conv.type== 'PAC':
                PGi_ren = sum(rs.PGi_ren*rs.gamma for rs in conv.Node_AC.connected_RenSource)
                QGi_ren = sum(rs.QGi_ren for rs in conv.Node_AC.connected_RenSource)
                PGi_opt = sum(gen.PGen for gen in conv.Node_AC.connected_gen)
                QGi_opt = sum(gen.QGen for gen in conv.Node_AC.connected_gen)
                if conv.Node_AC.stand_alone == True:
                    conv.P_AC = -(PGi_ren+PGi_opt-conv.Node_AC.PLi) 
                    conv.Q_AC = -(conv.Node_AC.QGi+QGi_opt+QGi_ren-conv.Node_AC.QLi+conv.Node_AC.Q_s_fx)
                else:
                    if conv.AC_type == 'Slack':
                        conv.P_AC = conv.Node_AC.P_INJ-(PGi_ren+PGi_opt-conv.Node_AC.PLi) 
                        conv.Q_AC = conv.Node_AC.Q_INJ-(conv.Node_AC.QGi+QGi_opt+QGi_ren-conv.Node_AC.QLi+conv.Node_AC.Q_s_fx)
                    if conv.AC_type == 'PV':
                        conv.Q_AC = conv.Node_AC.Q_INJ-(conv.Node_AC.QGi+QGi_opt-conv.Node_AC.QLi+conv.Node_AC.Q_s_fx)
                flow_conv_P_AC(grid,conv)
                s=1

        if QLimit == True:
            for conv in grid.Converters_ACDC:
                Converter_Qlimit(grid,conv)

        if grid.iter_num_seq == 0:
            s = 1
            grid.Check_SlacknDroop(change_slack2Droop)

        s = 1

        grid.Update_PQ_AC()
        grid.Update_P_DC()

        # Track DC power flow tolerance
        dc_tol = load_flow_DC(grid, tol_lim=internal_tol, Droop_PF=Droop_PF)
        tolerance_tracker['dc_pf_tolerances'].append(dc_tol)

        # Track converter tolerances
        conv_tolerances = []
        conv_names = []
        for conv in grid.Converters_ACDC:
            AC_node = conv.Node_AC
            DC_node = conv.Node_DC

            if conv.AC_type == 'PV':
                QGi_opt = sum(gen.QGen for gen in conv.Node_AC.connected_gen)
                QGi_ren = sum(rs.QGi_ren for rs in conv.Node_AC.connected_RenSource)
                conv.Q_AC = AC_node.Q_INJ-(AC_node.QGi+QGi_opt+QGi_ren-AC_node.QLi+AC_node.Q_s_fx)
            conv.U_s = AC_node.V
            conv.th_s = AC_node.theta
            
            # Get converter tolerance
            conv_tol = flow_conv(grid, conv, tol_lim=internal_tol*1e-4)
            conv_tolerances.append(conv_tol)
            conv_names.append(conv.name)
          
        tolerance_tracker['converter_tolerances'].append(conv_tolerances)
        if grid.iter_num_seq == 0:  # Store converter names only once
            tolerance_tracker['converter_names'] = conv_names
        
        Ps = np.copy(grid.Ps_AC)
        Ps_AC_new = np.copy(grid.Ps_AC_new)
        P_dif = Ps-Ps_AC_new

        tolerance = np.max(abs(P_dif))
        tolerance_tracker['sequential_iterations'].append(tolerance)
        
        # Store the current iteration's Ps values
        ps_iterations[grid.iter_num_seq, :] = Ps_AC_new.flatten()
        
        s = 1
        for node in grid.nodes_AC:
            node.P_s = Ps_AC_new[node.nodeNumber]
            grid.Ps_AC[node.nodeNumber] = np.copy(Ps_AC_new[node.nodeNumber])
        grid.Update_PQ_AC()

        # print(f'{iter_num} tolerance reached: {np.round(tolerance,decimals=12)}')
        grid.iter_num_seq += 1

    # Store final tolerance and convergence status
    tolerance_tracker['final_sequential_tolerance'] = tolerance
    
    if grid.iter_num_seq == maxIter:
        if tolerance > tol_lim*100:
            print('')
            print(
                f'Warning  Sequential flow did not converge in less than {maxIter} iterations')
            print(
                f'Lowest tolerance reached: {np.round(tolerance,decimals=6)}')
            tolerance_tracker['convergence_status']['sequential_converged'] = False
    
    grid.Line_AC_calc()
    grid.Line_AC_calc_exp()
    grid.Line_DC_calc()
    
    time_2=time.perf_counter()
    t = time_2-time_1
    
    return t, tolerance_tracker,ps_iterations

def Jacobian_DC(grid, V_DC, P,Droop_PF):
    grid.slack_bus_number_DC = []
    J = np.zeros((grid.nn_DC, grid.nn_DC))
    V = V_DC

    for i in range(grid.nn_DC):
        m = grid.nodes_DC[i].nodeNumber

        if grid.nodes_DC[i].type != 'Slack':
            for k in range(grid.nn_DC):
                n = grid.nodes_DC[k].nodeNumber

                if m != n:
                    if grid.Ybus_DC[m, n] != 0:
                        line = grid.get_lineDC_by_nodes(m, n)
                        G = line.np_line / line.R
                        J[m, n] = -line.pol * G * V[m] * V[n]
                else:
                    J[m, n] = P[m, 0]
                    if grid.nconv != 0:
                        if grid.nodes_DC[k].type == 'Droop' and Droop_PF:
                            J[m, n] += grid.nodes_DC[k].Droop_rate * V[m]

                    for a in range(grid.nn_DC):
                        if a != m:
                            if grid.Ybus_DC[m, a] != 0:
                                line = grid.get_lineDC_by_nodes(m, a)
                                G = line.np_line / line.R
                                J[m, n] += line.pol * G * V[m] * V[m]

        else:
            grid.slack_bus_number_DC.append(m)

    return J

def load_flow_DC(grid, tol_lim=1e-8, maxIter=100,Droop_PF=True):

    iter_num = 0

   
    V = np.zeros(grid.nn_DC)
    s = 1

    for node in grid.nodes_DC:
        V[node.nodeNumber] = node.V
    tol = 1
    
    
    
    P_known = np.copy(grid.P_DC+grid.Pconv_DC)
    while tol > tol_lim and iter_num < maxIter:
        iter_num += 1

        P = np.zeros((grid.nn_DC, 1))
        P1 = np.zeros((grid.nn_DC, 1))
        Pf = np.zeros((grid.nn_DC, 1))
        for node in grid.nodes_DC:

            i = node.nodeNumber
            for k in range(grid.nn_DC):
                if k != i:
                    if grid.Ybus_DC[i, k] != 0:
                        line = grid.get_lineDC_by_nodes(i, k)
                        G = line.np_line / line.R
                        P[i] += line.pol*V[i]*(V[i]-V[k])*G

        for node in grid.nodes_DC:
            if grid.nconv != 0:
                if node.type == 'Droop' and Droop_PF:
                    n = node.nodeNumber
                    Droop_change = (node.V_ini-V[n])*node.Droop_rate
                    P_known[n] = np.copy(grid.P_DC[n]+grid.Pconv_DC[n]) + Droop_change
                    s = 1        

        # print (P1)
        # print (P)
        # print('------')
        dPa = P_known-P

        J_DC = Jacobian_DC(grid,V, P,Droop_PF)

        if len(grid.slack_bus_number_DC) == 0:
            J_modified = J_DC
        else:
            J_modified = np.delete(
                np.delete(J_DC, grid.slack_bus_number_DC, 0), grid.slack_bus_number_DC, 1)
            dPa = np.delete(dPa, grid.slack_bus_number_DC, 0)

        dV_V = np.linalg.solve(J_modified, dPa)

        # Recall the updated voltage vector into the correct place
        k = 0  # Index for dV vector
        for i in range(grid.nn_DC):
            if grid.nodes_DC[i].type != 'Slack':
                dV = dV_V[k].item()*V[i]
                V[i] += dV
                k += 1  # Move to the next element in dV
        tol = max(abs(dPa))
        # print(f"Iteration {iter_num}, Max Voltage Change: {max(abs(dV))}, tolerance: {tol}")

        if iter_num == maxIter:
            print('')
            print(f'Warning  load flow DC did not converge in {maxIter} iterations')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=6)}')

    grid.iter_flow_DC.append(iter_num)

    grid.V_DC = V

    for node in grid.nodes_DC:
        i = node.nodeNumber
        for k in range(grid.nn_DC):
            if k != i:
                if grid.Ybus_DC[i, k] != 0:
                    line = grid.get_lineDC_by_nodes(i, k)
                    G = line.np_line / line.R
                    Pf[i] += line.pol*V[i]*(V[i]-V[k])*G
        grid.nodes_DC[i].V = V[i]
        node.P_INJ = Pf[i].item()
    dPa = P_known-Pf


    grid.P_DC_INJ = np.vstack([node.P_INJ for node in grid.nodes_DC])

    if grid.nconv != 0:

        for conv in grid.Converters_ACDC:
            n = conv.Node_DC.nodeNumber
            if conv.type== 'Droop' and Droop_PF:
                conv.P_DC         = P_known[n].item()-grid.P_DC[n].item()
                conv.Node_DC.Pconv= P_known[n].item()-grid.P_DC[n].item()
                s = 1
            elif conv.type== 'Slack':
                conv.Node_DC.Pconv = Pf[n].item()-grid.P_DC[n].item()
                conv.P_DC          = Pf[n].item()-grid.P_DC[n].item()
                s = 1
    grid.Update_P_DC()
    s = 1
    return tol
def Jacobian_AC(grid, Voltages, Angles,P,Q):
    grid.slack_bus_number_AC = []

    V = Voltages
    th = Angles
    
    slack_indices = np.array([i for i, node in enumerate(grid.nodes_AC) if node.type == 'Slack'], dtype=int)
    pv_indices = np.array([i for i, node in enumerate(grid.nodes_AC) if node.type == 'PV'], dtype=int)
    pq_indices = np.array([i for i, node in enumerate(grid.nodes_AC) if node.type == 'PQ'], dtype=int)
    non_slack_indices = np.sort(np.concatenate((pv_indices, pq_indices)))

    
    grid.slack_bus_number_AC = [grid.nodes_AC[i].nodeNumber for i in slack_indices]

    Gm = np.real(grid.Ybus_AC_full)
    Bm = np.imag(grid.Ybus_AC_full)

    # Precompute angle differences and trigonometric values
    angle_diff = th[:, None] - th[None, :]
    sin_theta = np.sin(angle_diff)
    cos_theta = np.cos(angle_diff)
    
   
    # Compute non-diagonal elements of J_11
    J_11 = V[:, None] * V[None, :] * (Gm * sin_theta - Bm * cos_theta)
    np.fill_diagonal(J_11, -Q - V**2 * Bm.diagonal())
    J_11 = J_11[np.ix_(non_slack_indices, non_slack_indices)]
    

    J_12 = V[:, None] * (Gm * cos_theta + Bm * sin_theta)
    np.fill_diagonal(J_12, P / V + np.diag(Gm) * V)
    J_12 = J_12[np.ix_(non_slack_indices, pq_indices)]

    
    J_21 = -V[:, None] * V[None, :] * (Gm * cos_theta + Bm * sin_theta)
    np.fill_diagonal(J_21, P - V**2 * np.diag(Gm))
    J_21 = J_21[np.ix_(pq_indices, non_slack_indices)]
    
    
    
    J_22 = V[:, None] * (Gm * sin_theta - Bm * cos_theta)
    np.fill_diagonal(J_22, Q / V - np.diag(Bm) * V)
    J_22 = J_22[np.ix_(pq_indices, pq_indices)]
    

    J_AC = np.vstack((np.hstack((J_11, J_12)), np.hstack((J_21, J_22))))

    return J_AC






def load_flow_AC(grid, tol_lim=1e-8, maxIter=100):

    Pnet = np.copy(grid.P_AC+grid.Ps_AC)
    Qnet = np.copy(grid.Q_AC+grid.Qs_AC)

    # number of different node types
    nps = len(grid.slack_nodes)

    V = np.array([node.V for node in grid.nodes_AC])
    angles = np.array([node.theta for node in grid.nodes_AC])
    
    G = np.real(grid.Ybus_AC_full)
    B = np.imag(grid.Ybus_AC_full)

    
    tol = 1
    iter_num = 0
    while tol > tol_lim and iter_num < maxIter:
        iter_num += 1

        P = np.zeros((grid.nn_AC, 1))
        Q = np.zeros((grid.nn_AC, 1))
        
        # Compute pairwise angle differences
        angle_diff = angles[:, None] - angles[None, :]  # Shape: (nn_AC, nn_AC)
    
        # Compute power components
        cos_term = np.cos(angle_diff)
        sin_term = np.sin(angle_diff)
        
        P = V[:, None] * V[None, :] * (G * cos_term + B * sin_term)
        Q = V[:, None] * V[None, :] * (G * sin_term - B * cos_term)
    
        # Sum across rows to get the net P and Q for each node
        P = P.sum(axis=1)
        Q = Q.sum(axis=1)
        
        # for node in grid.nodes_AC:
        #     i = node.nodeNumber
        #     for k in range(grid.nn_AC):
        #         G = np.real(grid.Ybus_AC[i, k])
        #         B = np.imag(grid.Ybus_AC[i, k])
        #         P[i] += V[i]*V[k] * \
        #             (G*np.cos(angles[i]-angles[k]) +
        #              B*np.sin(angles[i]-angles[k]))
        #         Q[i] += V[i]*V[k] * \
        #             (G*np.sin(angles[i]-angles[k]) -
        #              B*np.cos(angles[i]-angles[k]))


        # Calculate changes in specified active and reactive power
        dPa = Pnet- P[:, None]
        dQa = Qnet- Q[:, None]
        k = 0

        J_AC = Jacobian_AC(grid,V, angles,P,Q)

        Q_del = []
        for node in grid.nodes_AC:
            i = node.nodeNumber
            if node.type != 'PQ':
                Q_del.append(i)

        dP = np.delete(dPa, grid.slack_bus_number_AC, axis=0)
        dQ = np.delete(dQa, Q_del, axis=0)

        M = np.vstack((dP, dQ))

        X = np.linalg.solve(J_AC, M)

        # Check for NaN values in the array
        nan_indices = np.isnan(X)

        # Get the indices of NaN values
        nan_indices = np.where(nan_indices)[0]

        if nan_indices.size > 0:
            print("Linear results not avialable for AC PF")
            sys.exit()
        dTh = X[0:(grid.nn_AC-nps)]
        dV = X[grid.nn_AC-nps:]
      
        # Recall the updated voltage vector into the correct place
        k = 0  # Index for dV vector
        for i in range(grid.nn_AC):
            if grid.nodes_AC[i].type != 'Slack':
                s = 1
                # grid.nodes_AC[i].theta += dTh[k].item()
                angles[i] += dTh[k].item()
                k += 1  # Move to the next element in dTh
        k = 0  # Index for dV vector
        for i in range(grid.nn_AC):
            if grid.nodes_AC[i].type == 'PQ':
                # grid.nodes_AC[i].V += dV[k].item()
                V[i] += dV[k].item()
                k += 1  # Move to the next element in dV

        # for node in grid.nodes:
        #      V[node.nodeNumber]= node.V_iter
        #      angles[node.nodeNumber] = node.theta_iter

        tol = max(abs(M))
        if iter_num == maxIter:
            print('')
            print(f'Warning  load flow AC did not converge')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=int(-np.log10(tol_lim)))}')

    grid.iter_flow_AC.append(iter_num)

    grid.V_AC = V
    grid.Theta_V_AC = angles

    grid.voltage_violation = 0
    Diff = np.abs(V-1)

    grid.dif = max(Diff)

    if grid.dif > 0.11:
        grid.voltage_violation = 1

    V_violation = grid.voltage_violation
    Pf = np.zeros((grid.nn_AC, 1))
    Qf = np.zeros((grid.nn_AC, 1))
    for node in grid.nodes_AC:
        i = node.nodeNumber
        for k in range(grid.nn_AC):
            G = np.real(grid.Ybus_AC_full[i, k])
            B = np.imag(grid.Ybus_AC_full[i, k])
            Pf[i] += V[i]*V[k] * \
                (G*np.cos(angles[i]-angles[k]) +
                 B*np.sin(angles[i]-angles[k]))
            Qf[i] += V[i]*V[k] * \
                (G*np.sin(angles[i]-angles[k]) -
                 B*np.cos(angles[i]-angles[k]))
    Sf = Pf+1j*Qf

    for node in grid.nodes_AC:
        i = node.nodeNumber
        node.P_INJ = Pf[i].item()
        node.Q_INJ = Qf[i].item()
        node.V     = V[i].item()
        node.theta = angles[i].item()
    grid.P_AC_INJ = np.vstack([node.P_INJ for node in grid.nodes_AC])
    grid.Q_INJ = np.vstack([node.Q_INJ for node in grid.nodes_AC])
    s=1
    return tol
def flow_conv_P_AC(grid, conv):
    Us = conv.Node_AC.V
    th_s = conv.Node_AC.theta

    P_AC = conv.P_AC
    Q_AC = conv.Q_AC

    Ztf = conv.Ztf
    Zc = conv.Zc
    Zf = conv.Zf

    Us_cart = pol2cartz(Us, th_s)
    Ss_cart = P_AC+1j*Q_AC

    Is = np.conj(Ss_cart/Us_cart)

    if Zf != 0:
        Uf_cart = Us_cart+Ztf*Is
        Ic_cart = Us_cart/Zf+Is*(Zf+Ztf)/Zf
        Uc_cart = Uf_cart+Zc*Ic_cart
        
    else:
        Uf_cart = 0 + 1j*0
        Ic_cart = Is
        Uc_cart = Us_cart+(Ztf+Zc)*Ic_cart
        
        # else:
        #     [Uc, th_c] = [Us, th_s]
    [Uc, th_c] = cartz2pol(Uc_cart)
    [Uf, th_f] = cartz2pol(Uf_cart)
    [Ic, th_Ic] = cartz2pol(Ic_cart)
    

    Sc = Uc_cart*np.conj(Ic_cart)

    Pc = np.real(Sc)
    
    if conv.power_loss_model == 'MMC':
         
         P_loss,I= mmc_loss(conv,Pc)
        
    else:
        if conv.P_AC > 0:  # DC to AC
            P_loss = conv.a_conv+conv.b_conv*Ic+conv.c_inver*Ic*Ic
        else:  # AC to DC
            P_loss = conv.a_conv+conv.b_conv*Ic+conv.c_rect*Ic*Ic

    P_DC = -Pc-P_loss

    conv.P_loss = P_loss
    conv.P_DC = P_DC
    conv.U_f = Uf
    conv.U_c = Uc
    conv.th_f = th_f
    conv.th_c = th_c
    conv.Node_DC.Pconv = P_DC
    conv.Node_AC.P_s = P_AC
    conv.Ic = Ic
    s=1

def Jacobian_conv_notransformer(grid, conv, U_c, Pc, Qc, Ps, Qs):
    J_conv = np.zeros((2, 2))

    # dPc/dTheta_c
    J_conv[0, 0] = -Qc-conv.Bc*U_c*U_c

    # U_C*dPc/dUc
    J_conv[0, 1] = Pc+conv.Gc*U_c*U_c

    # dQs/dThetac
    J_conv[1, 0] = -Ps-conv.Gc*conv.U_s*conv.U_s

    # Uc*dQs/dU_c
    J_conv[1, 1] = Qs-(conv.Bf+conv.Bc)*conv.U_s*conv.U_s

    return J_conv

def Jacobian_conv_no_Filter(grid, conv, U_c, Pc, Qc, Ps, Qs):
    J_conv = np.zeros((2, 2))

    # dPc/dTheta_c
    J_conv[0, 0] = -Qc-conv.Bc*U_c*U_c

    # U_C*dPc/dUc
    J_conv[0, 1] = Pc+conv.Gc*U_c*U_c

    # dQs/dThetac
    J_conv[1, 0] = -Ps-conv.Gc*conv.U_s*conv.U_s

    # Uc*dQs/dU_c
    J_conv[1, 1] = Qs-conv.Bc*conv.U_s*conv.U_s

    return J_conv

def Jacobian_conv(grid, conv, Qcf, Qsf, Pcf, Psf, U_f, U_c, Pc, Qc, Ps, Qs):
    J_conv = np.zeros((4, 4))

    # dPc/dTheta_c
    J_conv[0, 0] = -Qc-conv.Bc*U_c*U_c

    # dPc/dTheta_f
    J_conv[0, 1] = Qc+conv.Bc*U_c*U_c

    # U_C*dPc/dUc
    J_conv[0, 2] = Pc+conv.Gc*U_c*U_c

    # U_f*dPc/dUf
    J_conv[0, 3] = Pc-conv.Gc*U_c*U_c

    # dQs/dThetaf
    J_conv[1, 1] = -Ps-conv.Gtf*conv.U_s*conv.U_s

    # Uf*dQs/dU_f
    J_conv[1, 3] = Qs-conv.Btf*conv.U_s*conv.U_s

    # dF1/dTheta c
    J_conv[2, 0] = Qcf-conv.Bc*U_f*U_f

    # dF1/dTheta f
    J_conv[2, 1] = -Qcf+Qsf+(conv.Bc+conv.Btf)*U_f*U_f

    #Uc *dF1/dUc
    J_conv[2, 2] = Pcf+conv.Gc*U_f*U_f

    # Uf*dF1/dUf
    J_conv[2, 3] = Pcf-Psf-(conv.Gc+conv.Gtf)*U_f*U_f

    # dF2/dTheta c
    J_conv[3, 0] = -Pcf-conv.Gc*U_f

    # dF2/dTheta f
    J_conv[3, 1] = Pcf-Psf+(conv.Gc+conv.Gtf)*U_f*U_f

    #Uc *dF2/dUc
    J_conv[3, 2] = Qcf-conv.Bc*U_f*U_f

    # Uf*dF2/dUf
    J_conv[3, 3] = Qcf-Qsf+(conv.Bc+conv.Btf+2*conv.Bf)*U_f*U_f

    return J_conv

def flow_conv(grid, conv, tol_lim=1e-12, maxIter=20):

    if conv.Bf == 0:
        tol = flow_conv_no_filter(grid,conv, tol_lim, maxIter)

    elif conv.Gtf == 0:

        tol = flow_conv_no_transformer(grid,conv, tol_lim, maxIter)

    else:

        tol = flow_conv_complete(grid,conv, tol_lim, maxIter)

    return tol

def flow_conv_no_filter(grid, conv, tol_lim, maxIter):
    
    Ztf = conv.Ztf / conv.np_conv
    Zc = conv.Zc / conv.np_conv

    Zeq = Ztf+Zc
     
    Uc = conv.U_c
    th_c = conv.th_c

    Pc_known = -np.copy(conv.P_DC)
    Qs_known = conv.Q_AC
    Us = conv.U_s
    th_s = conv.th_s

    tol2 = 1

    while tol2 > tol_lim:
        tol = 1
        iter_num = 0
        
        if Zeq != 0:
            Yeq = 1/Zeq
            Gc = np.real(Yeq)
            Bc = np.imag(Yeq)
            while tol > tol_lim and iter_num < maxIter:
                
                iter_num += 1
    
                Ps = -Us*Us*Gc+Us*Uc * \
                    (Gc*np.cos(th_s-th_c)+Bc*np.sin(th_s-th_c))
                Qs = Us*Us*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)-Bc*np.cos(th_s-th_c))
    
                Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
                Qc = -Uc*Uc*Bc+Us*Uc * \
                    (Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))
    
                J_conv = Jacobian_conv_no_Filter(grid,conv, Uc, Pc, Qc, Ps, Qs)
    
                dPc = Pc_known-Pc
                dQs = Qs_known-Qs
    
                M = np.array([dPc, dQs])
    
                X = np.linalg.solve(J_conv, M)
    
                th_c += X[0].item()
    
                Uc += X[1].item()*Uc
    
                tol = max(abs(M))
    
            Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
            Qc = -Uc*Uc*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))
        else:
            Uc  =Us 
            th_c=th_s
            Pc  = Pc_known
            Qc  = Qs_known
            
        if iter_num > maxIter:
            print('')
            print(f'Warning  converter {conv.name} did not converge')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=6)}')

        
        if conv.power_loss_model == 'MMC':
           
            P_loss,I= mmc_loss(conv,Pc)
           
        else:

            Ic = np.sqrt(Pc*Pc+Qc*Qc)/Uc
        
            if conv.P_DC < 0:  # DC to AC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_inver*Ic*Ic/ conv.np_conv
            else:  # AC to DC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_rect*Ic*Ic/ conv.np_conv
        
        Pc_new = -conv.P_DC-P_loss

        tol2 = abs(Pc_known-Pc_new)
        # print(tol2)
        Pc_known = Pc_new

    if Zeq != 0:
        Yeq = 1/Zeq
        Gc = np.real(Yeq)
        Bc = np.imag(Yeq)
        Ps = -Us*Us*Gc+Us*Uc*(Gc*np.cos(th_s-th_c)+Bc*np.sin(th_s-th_c))
        Qs = Us*Us*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)-Bc*np.cos(th_s-th_c))
    
        Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
        Qc = -Uc*Uc*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))
    else:
        Ps=Pc
        Qs=Qc
    if conv.type!= 'PAC':
        conv.P_AC = Ps
    conv.Q_AC = Qs
    
    conv.Pc = Pc
    conv.Qc = Qc
    
    conv.U_c = Uc
   
    conv.th_c = th_c
    
    Ps_old = conv.Node_AC.P_s
    conv.P_loss = P_loss
    conv.P_loss_tf = abs(Ps-Pc)
    n = conv.Node_AC.nodeNumber
    
    grid.Ps_AC_new[n] += Ps
    s=1
    return tol2

def flow_conv_no_transformer(grid, conv, tol_lim, maxIter):
    Uc = conv.U_c
    Gc = conv.Gc

    th_c = conv.th_c
    

    Bf = conv.Bf    * conv.np_conv
    Gc  = conv.Gc   * conv.np_conv
    Bc  = conv.Bc   * conv.NumConv
    Bf  = conv.Bf   * conv.np_conv
    
    
    Pc_known = -np.copy(conv.P_DC)
    Qs_known = np.copy(conv.Q_AC)
    Us = conv.U_s
    th_s = conv.th_S

    tol2 = 1

    while tol2 > tol_lim:
        tol = 1
        iter_num = 0
        while tol > tol_lim and iter_num < maxIter:
            iter_num += 1
            Bcf = Bc+Bf

            Ps = -Us*Us*Gc+Us*Uc * \
                (Gc*np.cos(th_s-th_c)+Bc*np.sin(th_s-th_c))
            Qs = Us*Us*Bcf+Us*Uc * \
                (Gc*np.sin(th_s-th_c)-Bc*np.cos(th_s-th_c))

            Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
            Qc = -Uc*Uc*Bc+Us*Uc * \
                (Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))

            J_conv = Jacobian_conv_notransformer(grid,conv, Uc, Pc, Qc, Ps, Qs)

            dPc = Pc_known-Pc
            dQs = Qs_known-Qs

            M = np.array([dPc, dQs])

            X = np.linalg.solve(J_conv, M)

            th_c += X[0].item()
            Uc += X[1].item()*Uc

            tol = max(abs(M))

        Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
        Qc = -Uc*Uc*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))

        if iter_num > maxIter:
            print('')
            print(f'Warning  converter {conv.name} did not converge')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=6)}')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=6)}')
            
        if conv.power_loss_model == 'MMC':
            
            
            P_loss,I= mmc_loss(conv,Pc)
            
        else:

            Ic = np.sqrt(Pc*Pc+Qc*Qc)/Uc
        
            if conv.P_DC < 0:  # DC to AC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_inver*Ic*Ic/ conv.np_conv
            else:  # AC to DC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_rect*Ic*Ic/ conv.np_conv    
            
        

        Pc_new = -conv.P_DC-P_loss

        tol2 = abs(Pc_known-Pc_new)

        Pc_known = np.copy(Pc_new)

        s = 1

    Ps = -Us*Us*Gc+Us*Uc*(Gc*np.cos(th_s-th_c)+Bc*np.sin(th_s-th_c))
    Qs = Us*Us*Bcf+Us*Uc*(Gc*np.sin(th_s-th_c)-Bc*np.cos(th_s-th_c))

    Pc = Uc*Uc*Gc-Us*Uc*(Gc*np.cos(th_s-th_c)-Bc*np.sin(th_s-th_c))
    Qc = -Uc*Uc*Bc+Us*Uc*(Gc*np.sin(th_s-th_c)+Bc*np.cos(th_s-th_c))

    if conv.type!= 'PAC':
        conv.P_AC = Ps
    conv.Q_AC = Qs
    
    conv.Pc = Pc
    conv.Qc = Qc

    conv.U_c = Uc
    conv.th_c = th_c
   
    conv.P_loss = P_loss
    conv.P_loss_tf = abs(Ps-Pc)
  
    grid.Ps_AC_new[conv.Node_AC.nodeNumber] += Ps
    return tol2
   
def flow_conv_complete(grid, conv, tol_lim, maxIter):
    Uc = conv.U_c
    
    Uf = conv.U_f
    
    th_f = conv.th_f
    th_c = conv.th_c
   
    Bf = conv.Bf    * conv.np_conv
    Gc  = conv.Gc   * conv.np_conv
    Bc  = conv.Bc   * conv.np_conv
    Gtf = conv.Gtf  * conv.np_conv
    Btf = conv.Btf  * conv.np_conv
    Bf  = conv.Bf   * conv.np_conv
    
    
    Pc_known = -np.copy(conv.P_DC)
    Qs_known = conv.Q_AC
    Us = conv.U_s
    th_s = conv.th_s

    tol2 = 1

    while tol2 > tol_lim:
        tol = 1
        iter_num = 0
        while tol > tol_lim and iter_num < maxIter:
            iter_num += 1

            Ps = -Us*Us*Gtf+Us*Uf * \
                (Gtf*np.cos(th_s-th_f)+Btf*np.sin(th_s-th_f))
            Qs = Us*Us*Btf+Us*Uf * \
                (Gtf*np.sin(th_s-th_f)-Btf*np.cos(th_s-th_f))

            Pc = Uc*Uc*Gc-Uf*Uc*(Gc*np.cos(th_f-th_c)-Bc*np.sin(th_f-th_c))
            Qc = -Uc*Uc*Bc+Uf*Uc * \
                (Gc*np.sin(th_f-th_c)+Bc*np.cos(th_f-th_c))

            Psf = Uf*Uf*Gtf-Uf*Us * \
                (Gtf*np.cos(th_s-th_f)-Btf*np.sin(th_s-th_f))
            Qsf = -Uf*Uf*Btf+Uf*Us * \
                (Gtf*np.sin(th_s-th_f)+Btf*np.cos(th_s-th_f))

            Pcf = -Uf*Uf*Gc+Uf*Uc * \
                (Gc*np.cos(th_f-th_c)+Bc*np.sin(th_f-th_c))
            Qcf = Uf*Uf*Bc+Uf*Uc * \
                (Gc*np.sin(th_f-th_c)-Bc*np.cos(th_f-th_c))

            Qf = -Uf*Uf*Bf

            J_conv = Jacobian_conv(grid,conv, Qcf, Qsf, Pcf, Psf, Uf, Uc, Pc, Qc, Ps, Qs)

            F1 = Pcf-Psf
            F2 = Qcf-Qsf-Qf
            dPc = Pc_known-Pc
            dQs = Qs_known-Qs

            M = np.array([dPc, dQs, -F1, -F2])

            X = np.linalg.solve(J_conv, M)

            th_c += X[0].item()
            th_f += X[1].item()
            Uc += X[2].item()*Uc
            Uf += X[3].item()*Uf

            tol = max(abs(M))

        Pc = Uc*Uc*Gc-Uf*Uc*(Gc*np.cos(th_f-th_c)-Bc*np.sin(th_f-th_c))
        Qc = -Uc*Uc*Bc+Uf*Uc*(Gc*np.sin(th_f-th_c)+Bc*np.cos(th_f-th_c))

        if iter_num > maxIter:
            print('')
            print(f'Warning  converter {conv.name} did not converge')
            print(f'Lowest tolerance reached: {np.round(tol,decimals=6)}')

        if conv.power_loss_model == 'MMC':

    
            P_loss,I= mmc_loss(conv,Pc)
         
        else:

            Ic = np.sqrt(Pc*Pc+Qc*Qc)/Uc
        
            if conv.P_DC < 0:  # DC to AC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_inver*Ic*Ic/ conv.np_conv
            else:  # AC to DC
                P_loss = conv.a_conv* conv.np_conv+conv.b_conv*Ic+conv.c_rect*Ic*Ic/ conv.np_conv
        # print(f'{conv.name} - {P_loss}')
        Pc_new = -conv.P_DC-P_loss

        tol2 = abs(Pc_known-Pc_new)

        Pc_known = np.copy(Pc_new)

    Ps = -Us*Us*Gtf+Us*Uf*(Gtf*np.cos(th_s-th_f)+Btf*np.sin(th_s-th_f))
    Qs = Us*Us*Btf+Us*Uf*(Gtf*np.sin(th_s-th_f)-Btf*np.cos(th_s-th_f))
    # Pc=  Uc*Uc*Gc-Uf*Uc*(Gc*np.cos(th_f-th_c)-Bc*np.sin(th_f-th_c))
    # Qc= -Uc*Uc*Bc+Uf*Uc*(Gc*np.sin(th_f-th_c)+Bc*np.cos(th_f-th_c))
    # CHECK THIs
    if conv.type!= 'PAC':
        conv.P_AC = Ps
    conv.Q_AC = Qs
    
    conv.Pc = Pc
    conv.Qc = Qc

    conv.U_c = Uc
    conv.U_f = Uf
    conv.th_c = th_c
    conv.th_f = th_f

    conv.P_loss = P_loss
    conv.P_loss_tf = abs(Ps-Pc)
    

    conv.Ic =  np.sqrt(Pc*Pc+Qc*Qc)/Uc
    
    grid.Ps_AC_new[conv.Node_AC.nodeNumber] += Ps
    s=1
    return tol2
def mmc_loss(conv,Pc):
    Vdc = conv.Node_DC.V
    Ra = conv.ra
    
    I = (-Vdc +np.sqrt(Vdc**2-4*Ra*Pc/3))/(-2*Ra)

    P_loss = 3*I**2*Ra
    P_loss2 = 6*I**2*Ra
    conv.Vsum = -Ra*I + Vdc
    return P_loss,I

def Converter_Qlimit(grid, conv):

    Us = conv.Node_AC.V
    th_s = conv.Node_AC.theta

    conj_Ztf = np.conj(conv.Ztf/ conv.np_conv)
    conj_Zc = np.conj(conv.Zc/ conv.np_conv)
    conj_Zf = np.conj(conv.Zf/ conv.np_conv)

    S_max = conv.MVA_max/grid.S_base
    Icmax = S_max #assumes V = 1

    Ps = conv.P_AC

    S0 = 0
    S0v = 0
    Y1 = 0
    if conv.Z1 != 0:
        Y1 = (1/conv.Z1)*conv.np_conv

    if conv.Zf != 0:
        r = Us*Icmax*np.abs(conj_Zf/(conj_Zf+conj_Ztf))

        S0 = -Us**2*(1/(conj_Zf+conj_Ztf))
        Y2 = (1/conv.Z2)*conv.np_conv
        S0v = -Us**2*(np.conj(Y1)+np.conj(Y2))
        rVmin = Us*conv.Ucmin*np.abs(Y2)
        rVmax = Us*conv.Ucmax*np.abs(Y2)
    elif conj_Ztf+conj_Zc ==0:
        
        
        S0 = 0
        S0v = 0
        r = Us*Icmax
        rVmin = Us*conv.Ucmin
        rVmax = Us*conv.Ucmax
        s=1
    else:
        r = Us*Icmax
        S0v = -Us**2*(1/(conj_Ztf+conj_Zc))
        rVmin = Us*conv.Ucmin*np.abs(1/(conj_Ztf+conj_Zc))
        rVmax = Us*conv.Ucmax*np.abs(1/(conj_Ztf+conj_Zc))

    Q0 = np.imag(S0)
    Q0V = np.imag(S0v)

    Po = np.real(S0)

    sqrt = r**2-(Ps-Po)**2
    if sqrt < 0:
        print(f'Converter {conv.name} is over current capacity')

    Qs_plus  = Q0+np.sqrt(r**2-(Ps-Po)**2)
    Qs_minus = Q0-np.sqrt(r**2-(Ps-Po)**2)

    Qs_plusV = Q0V+np.sqrt(rVmax**2-(Ps-Po)**2)
    Qs_minusV = Q0V-np.sqrt(rVmin**2-(Ps-Po)**2)

    Qs_max = min(Qs_plus, Qs_plusV)
    Qs_min = max(Qs_minus, Qs_minusV)

    name = conv.name

    conv.Node_AC.Q_min = Qs_minus
    conv.Node_AC.Q_max = Qs_plus

    AC_node = conv.Node_AC.nodeNumber

    if conv.AC_type == 'PV' or conv.AC_type == 'Slack':
        conv.Node_AC.Q_s = (grid.Q_INJ[AC_node]-grid.Q_AC[AC_node]).item()
        Q_req = conv.Node_AC.Q_s
    else:
        Q_req = conv.Q_AC
        # conv.Node_AC.Q_s= (grid.Q_INJ[AC_node]-grid.Q_AC[AC_node]).item()-Q_req

    if Q_req > Qs_max or Q_req < Qs_min:

        print('-----------')
        print(f'{conv.name}  CONVERTER LIMIT circle REACHED')
        print('-----------')
        if conv.Node_AC.type == 'Slack':
            print(f' Limiting Q from converter')
            print(f' External reactive compensation needed at node {conv.Node_AC.name}')
            if Q_req > Qs_plus:
                conv.Node_AC.Q_s = Qs_max
                conv.Node_AC.Q_AC = Q_req-Qs_max
            elif Q_req < Qs_minus:
                conv.Node_AC.Q_s = Qs_min
                conv.Node_AC.Q_AC = Q_req-Qs_min
                s = 1

        else:
            print(
                f'Limiting Q from converter and changing AC node {conv.Node_AC.name} to PQ')
            conv.Node_AC.type = 'PQ'
            if Q_req > Qs_max:
                conv.Node_AC.Q_s = Qs_max
            elif Q_req < Qs_min:
                conv.Node_AC.Q_s = Qs_min
        conv.AC_type = 'PQ'
        

        