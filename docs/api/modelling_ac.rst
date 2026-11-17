AC System Modelling
===================

.. _AC_node_modelling:

AC node
^^^^^^^

.. themed-figure:: ac_node_model
   :width: 250
   :alt: AC node model
   :align: center

   AC node equivalent circuit with voltage source and impedance

The active and reactive power injections at the AC node are given by [1]_:

Non-linear model
~~~~~~~~~~~~~~~~

.. math::
    :label: eq:PnodeAC

    \begin{align}
      P_{net}^{ac} &= P_{flow}^{ac} \\
      P_{net}^{ac} &= \sum P_{g_i} +  \sum \gamma_{rg_i}P_{rg_i} - P_{l_i} + \sum P_{cn_i} \\
      P_{flow}^{ac} &= \sum_{k \in \mathcal{N}_{ac}} |V_i||V_k| [ G_{ik} \cos(\theta_i-\theta_k) + B_{ik} \sin(\theta_i-\theta_k) ] \qquad \forall i \in \mathcal{N}_{ac} 
    \end{align}

.. math::
    :label: eq:QnodeAC

    \begin{align}
      Q_{net}^{ac} &= Q_{flow}^{ac} \\
      Q_{net}^{ac} &=  \sum Q_{g_i} + \sum Q_{rg_i} -Q_{l_i}+\sum Q_{cn_{i}} \\
      Q_{flow}^{ac} &= \sum_{k \in \mathcal{N}_{ac}} |V_i||V_k|[G_{ik} \sin(\theta_i-\theta_k)-B_{ik} \cos(\theta_i-\theta_{k})] \qquad \forall i \in \mathcal{N}_{ac} 
    \end{align}

.. math::
    :label: eq:Vac

    \begin{align}
        V_{min} \leq V_{i} \leq V_{max}  & \qquad \forall i \in \mathcal{N}_{ac}  \\
        \theta_{min} \leq \theta_i \leq \theta_{max}  & \qquad \forall i \in \mathcal{N}_{ac}
    \end{align}


The AC node is modeled using a complex voltage phasor :math:`V_i = V_i \angle \theta_i` where:

* :math:`V_i` is the voltage magnitude in pu
* :math:`\theta_i` is the voltage angle
* :math:`P_{rg}` is the active power injection of renewable generation in pu
* :math:`Q_{rg}` is the reactive power injection of renewable generation in pu
* :math:`P_{cn}` is the active power injection of converter in pu
* :math:`Q_{cn}` is the reactive power injection of converter in pu
* :math:`P_g` is the active power injection of generator in pu
* :math:`S_l` is the complex power demand in pu

Linear model
~~~~~~~~~~~~

In the linear OPF stack (:doc:`L_models`), the AC node uses a B-:math:`\theta`
active-power balance. Reactive power is not included in the network equations.

.. math::
    :label: eq:PnodeAC_L

    \begin{align}
      P_{net}^{ac} &= P_{flow}^{ac} \\
      P_{net}^{ac} &= \sum P_{g_i} + \sum \gamma_{rg_i}P_{rg_i} - P_{l_i}
                    + \sum P_{cn_i} \\
      P_{flow}^{ac} &= \sum_{k \in \mathcal{N}_{ac}}
        -\Im(Y_{ik})\,(\theta_i-\theta_k)
        \qquad \forall i \in \mathcal{N}_{ac} \\
      \theta_{i} &= 0
        \qquad \forall i \in \mathcal{N}_{ac}^{\mathrm{slack}}
    \end{align}

Optional flexible injections (storage, electrolyser, heat pump) enter
:math:`P_{net}^{ac}` with the same sign convention as in the nonlinear model.

Class Reference: :class:`pyflow_acdc.Classes.Node_AC`

.. autoclass:: pyflow_acdc.Node_AC
   :no-members:

Example Usage:

.. literalinclude:: ../../pyflow_tests/doc_examples/modelling_ac/01_ac_node.py
   :language: python
   :lines: 2-

        


.. _AC_branch_modelling:

AC branch
^^^^^^^^^

.. themed-figure:: ac_line_pi
   :width: 400
   :alt: AC line model
   :align: center

   AC line π-model

The AC branch is modeled with pi model from [1]_, [2]_ :

Non-linear model
~~~~~~~~~~~~~~~~

.. math::
    :label: eq:Ybusbranch

    Y_{bus-{branch}} = \begin{bmatrix}
        Y_{ff} & Y_{ft} \\
        Y_{tf} & Y_{tt}
    \end{bmatrix}
    = \begin{bmatrix}
        \frac{Y_s+Y_{sh}}{\mu^2} & -\frac{Y_s}{\mu e^{-j\tau}} \\
        -\frac{Y_s}{\mu e^{j\tau}} & Y_{s}+Y_{sh}
    \end{bmatrix}

.. math::
    :label: eq:YbusAC

    \begin{align}
        Y_{bus_{AC}}[i,i]&+= Y_{ff} + G_{r_i}+jB_{r_i}\\
        Y_{bus_{AC}}[i,k]&+= Y_{ft}\\
        Y_{bus_{AC}}[k,i]&+= Y_{tf}\\
        Y_{bus_{AC}}[k,k]&+= Y_{tt} +G_{r_k}+ jB_{r_k}
    \end{align}


.. math::
    :label: eq:S_ACrate

    \begin{align}
        P_{j,to}^2+Q_{j,to}^2 &\leq S_{j,rating}^2 \qquad \forall j \in \mathcal{B}_{ac}\\
        P_{j,from}^2+Q_{j,from}^2 &\leq S_{j,rating}^2  \qquad \forall j \in \mathcal{B}_{ac}
    \end{align}

Linear model
~~~~~~~~~~~~

In the linear OPF stack, AC branch flows are written from the branch
susceptance and voltage-angle difference:

.. math::
    :label: eq:PAC_branch_L

    \begin{align}
        P_{j,\mathrm{from}} &= -B_{ft}\,(\theta_{f}-\theta_{t}) \\
        P_{j,\mathrm{to}} &= -B_{tf}\,(\theta_{t}-\theta_{f}) \\
        |P_{j,\mathrm{from}}| &\leq S_{j,\mathrm{rating}}
          \qquad \forall j \in \mathcal{B}_{ac} \\
        |P_{j,\mathrm{to}}| &\leq S_{j,\mathrm{rating}}
          \qquad \forall j \in \mathcal{B}_{ac}
    \end{align}

with :math:`B_{ft}=\Im(Y_{ft})` and :math:`B_{tf}=\Im(Y_{tf})` taken from the
branch admittance matrix.

Class Reference: :class:`pyflow_acdc.Classes.Line_AC`

.. autoclass:: pyflow_acdc.Line_AC
   :no-members:

Example Usage:

.. literalinclude:: ../../pyflow_tests/doc_examples/modelling_ac/02_ac_branch.py
   :language: python
   :lines: 2-




Transmission Expansion Planning Modelling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In transmision expansion planning, each branch subject to modification is modeled independently in their power flow equations. The standard :math:`\pi`-model is used to represent branch through its corresponding branch admittance :math:`Y_{\text{bus-branch}}`.

.. math::
    :label: eq:PQ_branch

    \begin{align}
        S_{ik}& = P_{ik} + \text{j} Q_{ik} \\
        P_{ik} &= |V_i|^2 G_{ff} + |V_i||V_k| \left[ G_{ft} \cos(\theta_i - \theta_k) + B_{ft} \sin(\theta_i - \theta_k) \right] \\
        Q_{ik}&=-|V_i|^2 B_{ff}+|V_i||V_k|[G_{ft} \sin(\theta_i-\theta_k)-B_{ft} \cos(\theta_i-\theta_{k}) 
    \end{align}





.. _AC_expandable_branch:

AC expandable branch
~~~~~~~~~~~~~~~~~~~~

.. themed-figure:: ac_ybusbranch
   :width: 400
   :alt: AC expandable branch model
   :align: center

   AC expandable branch model

The AC expandable branch :math:`h` is modeled with in admittance matrix model from [4]_:


.. math::
    :label: eq:Seqexpbranch

    \begin{align}
        S_{h_\text{ik}\text{-eq}} &= n_h \cdot S_{h_\text{ik}} \\
        S_{h_\text{ki}\text{-eq}} &= n_h \cdot S_{h_\text{ki}}
    \end{align}
    
.. math::
    :label: eq:PQ_expandable

    \begin{align}
        P_{flow}^{ac} +=  \sum n_{h} P_{h_\text{ik}} \\
        Q_{flow}^{ac} +=  \sum n_{h} Q_{h_\text{ik}}
    \end{align}




Class Reference: :class:`pyflow_acdc.Classes.Exp_Line_AC`

Inherits from :class:`Line_AC` with the following additional attributes:

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Attribute
     - Type
     - Description
   * - ``base_cost``
     - float
     - Base cost of the line
   * - ``life_time``
     - float
     - Lifetime of the line
   * - ``np_line_b``
     - float
     - Base number of lines
   * - ``np_line_max``
     - float
     - Maximum number of lines

Where :math:`n_b \leq n_{max}`.

Note:

- The previous ``np_line_i`` attribute (used as a solver initialization / first guess) has been removed from the element classes.
- Solver initial values are now computed in the modelling layer (see ``get_TEP_variables``) and passed to Pyomo variables via the ``*_model_first_guess`` data structures.

.. _AC_reconducting_branch:

AC reconducting branch
~~~~~~~~~~~~~~~~~~~~~~

.. themed-figure:: ac_reconducting
   :width: 400
   :alt: AC expandable branch model
   :align: center

   AC reconducting branch model

The AC reconducting branch :math:`u` is modeled with in admittance matrix model from [4]_:


.. math::
    :label: eq:Seqrepbranch

    \begin{align}
        S_{u_\text{ik}\text{-eq}} &= (1-\xi_u)\cdot S_{u_\text{ik}} + \xi_u \cdot S_{u_\text{ik}}'  \\
        S_{u_\text{ki}\text{-eq}} &=(1-\xi_u)\cdot S_{u_\text{ki}} + \xi_u \cdot S_{u_\text{ki}}'
    \end{align}

.. math::
    :label: eq:PQ_reconducting

    \begin{align}
        P_{flow}^{ac} += \sum P_{u_\text{ik}\text{-eq}} \\
        Q_{flow}^{ac} += \sum  Q_{u_\text{ik}\text{-eq}}
    \end{align}



Class Reference: :class:`pyflow_acdc.Classes.rec_Line_AC`

Inherits from :class:`Line_AC` with the following additional attributes:

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Attribute
     - Type
     - Description
   * - ``r_new``
     - float
     - Resistance of the new conductor in pu
   * - ``x_new``
     - float
     - Reactance of the new conductor in pu
   * - ``g_new``
     - float
     - Conductance of the new conductor in pu
   * - ``b_new``
     - float
     - Susceptance of the new conductor in pu
   * - ``MVA_rating_new``
     - float
     - MVA rating of the new conductor
   * - ``Life_time``
     - float
     - Lifetime of the conductor
   * - ``base_cost``
     - float
     - Base cost of the conductor

.. _AC_conductor_size_selection:

AC conductor size selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. themed-figure:: ac_array
   :width: 400
   :alt: AC expandable branch model
   :align: center

   AC conductor size selection model

The AC conductor size selection :math:`a` is modeled with in admittance matrix model from [4]_:


.. math::
    :label: eq:array_case

    \begin{align}
        S_{a_\text{ik}\text{-eq}} &= \sum_{ \iota \in \mathcal{CT}} \left(\xi_{a,\iota}\cdot S_{a,\iota_\text{ik}} \right)  \\
        S_{a_\text{ki}\text{-eq}} &=\sum_{ \iota \in \mathcal{CT}}  \left( \xi_{a,\iota}\cdot S_{a,\iota_\text{ki}} \right) 
    \end{align}

.. math::
    :label: eq:PQ_array 

    \begin{align}
        P_{flow}^{ac} += \sum P_{a_\text{ik}\text{-eq}} \\
        Q_{flow}^{ac} += \sum Q_{a_\text{ik}\text{-eq}}
    \end{align}


        
For the branches $a$ an additional equality constraint is introduced to keep one type of branch per connection, such that :

.. math::
    :label: eq:ct_unique_constraint

    \sum_{n \in\mathcal{CT}} \xi_{a, n} = 1 \qquad \forall a \in \mathcal{E}_a 

.. math::
    :label: eq:Seqarraybranch

    S_{from_n-eq} = \xi_{a,n} \cdot S_{from_n}   \\
    S_{to_n-eq}   = \xi_{a,n} \cdot S_{to_n}

Additionally, to limit the number of branch types in the evaluated system, inequality constraints are included such that:

.. math::
    :label: eq:ct_constraints

    \begin{align}
        &\sum_{a\in\mathcal{E}_a} \xi_{a, n} \leq |\mathcal{E}_a| \cdot \nu_n \qquad \forall n \in \mathcal{CT} \\
        &\nu_n \leq \sum_{a\in\mathcal{E}_a} \xi_{a, n} \qquad\qquad\;  \forall n \in \mathcal{CT}  \\
        &\sum_{n\in \mathcal{CT}} \nu_n \leq \mathfrak{N}
    \end{align}


Class Reference: :class:`pyflow_acdc.Classes.Size_selection`

Inherits from :class:`Line_AC` with the following additional attributes:

.. list-table::
   :widths: 20 10 70
   :header-rows: 1

   * - Attribute
     - Type
     - Description
   * - ``fromNode``
     - :class:`Node_AC`
     - The starting node of the line
   * - ``toNode``
     - :class:`Node_AC`
     - The ending node of the line
   * - ``cable_types``
     - list
     - List of possible cable types for sizing
   * - ``active_config``
     - int
     - Index of the currently active cable configuration
   * - ``Length_km``
     - float
     - Length of the line in kilometers
   * - ``S_base``
     - float
     - Base power in MVA
   * - ``name``
     - str
     - Name of the line
   * - ``geometry``
     - str
     - Geometry of the line

Important to note that this class only takes in the cable types and not the line parameters. The parameters for these have to be uploaded as yalm files in the ``Cable_database`` folder.

**References**

.. [1] B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
       "An optimal power flow tool for AC/DC systems, applied to the analysis of the
       North Sea Grid for offshore wind integration" in IEEE Transactions on Power
       Systems, doi: 10.1109/TPWRS.2023.3533889.

.. [2] D. Zimmerman, C. E. Murillo-Sanchez, and R. J. Thomas, "MATPOWER: Steady-
       State Operations, Planning and Analysis Tools for Power Systems Research and
       Education," Power Systems, IEEE Transactions on, vol. 26, no. 1, pp. 12–19,
       Feb. 2011.

.. [4] B. C. Valerio, M. Cheah-Mane, V. A. Lacerda, P. Gebraad and O. Gomis-Bellmunt,
       "Transmission expansion planning for hybrid AC/DC grids using a
       Mixed-Integer Non-linear Programming approach"

