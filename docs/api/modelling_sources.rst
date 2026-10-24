Sources and Price Zones
=======================

Renewable Source
----------------

.. themed-figure:: ren_sources_model
   :width: 250
   :alt: Renewable source model
   :align: center

   Renewable source model

Non-linear model
~~~~~~~~~~~~~~~~

For all renewable sources:

.. math::
    :label: eq:Rgen

    \gamma_{rg}^{\min} \leq \gamma_{rg} \leq 1
      \qquad \forall rg \in \mathcal{RG}

For renewable sources connected to AC nodes:

.. math::
    :label: eq:Rgen_AC

    \begin{align}
        Q_{rg}^{\min} \leq Q_{rg} \leq Q_{rg}^{\max}
          & \qquad \forall rg \in \mathcal{RG}_{ac} \\
        (\gamma_{rg} P_{rg})^2 + Q_{rg}^2 \leq S_{rg,\mathrm{rating}}^{2}
          & \qquad \forall rg \in \mathcal{RG}_{ac}
    \end{align}

.. themed-figure:: ren_source_limits
   :width: 250
   :alt: Renewable source limits
   :align: center

   Renewable source limits

Linear model
~~~~~~~~~~~~

In the linear OPF stack (:doc:`L_models`), only the curtailment factor is
optimised. Reactive power and the apparent-power circle are omitted:

.. math::
    :label: eq:Rgen_L

    \gamma_{rg}^{\min} \leq \gamma_{rg} \leq 1
      \qquad \forall rg \in \mathcal{RG}

When the number of units :math:`n_{rg}` is an investment variable and
:math:`\gamma_{rg}^{\min} < 1`, the product :math:`\gamma_{rg} n_{rg}` is replaced
by the curtailed unit count :math:`y_{rg}`:

.. math::
    :label: eq:Rgen_L_y

    \begin{align}
        \gamma_{rg}^{\min}\, n_{rg} \leq y_{rg} \leq n_{rg}
          & \qquad \forall rg \in \mathcal{RG} \\
        P_{rg}^{inj} = P_{rg}\, y_{rg}
          & \qquad \forall rg \in \mathcal{RG}
    \end{align}

The curtailment factor is recovered as :math:`\gamma_{rg} = y_{rg} / n_{rg}` for
:math:`n_{rg} > 0`.

Class Reference: :class:`pyflow_acdc.Classes.Ren_Source`

.. autoclass:: pyflow_acdc.Ren_Source
   :no-members:

.. list-table::
   :widths: 20 50
   :header-rows: 1

   * - Type
     - Figure for folium plotting
   * - wind
     - .. image:: ../images/modelling/icons/wind.svg
         :width: 100
         :alt: Wind source icon
         :align: center
   * - offshore wind
     - .. image:: ../images/modelling/icons/offshore_wind.svg
         :width: 100
         :alt: Wind source icon
         :align: center
   * - onshore wind
     - .. image:: ../images/modelling/icons/onshore_wind.svg
         :width: 100
         :alt: Wind source icon
         :align: center
   * - solar
     - .. image:: ../images/modelling/icons/solar.svg
         :width: 100
         :alt: Solar source icon
         :align: center



.. _Generator_modelling:

Generator
---------

.. themed-figure:: gen_model
   :width: 250
   :alt: Generator model
   :align: center

   Generator model

Non-linear model
~~~~~~~~~~~~~~~~

.. math::
    :label: eq:gen

    \begin{align}
        P_{g}^{\min} \leq P_{g} \leq P_{g}^{\max}
          & \qquad \forall g \in \mathcal{G}_{ac} \\
        Q_{g}^{\min} \leq Q_{g} \leq Q_{g}^{\max}
          & \qquad \forall g \in \mathcal{G}_{ac} \\
        P_{g}^{2} + Q_{g}^{2} \leq S_{g,\mathrm{rating}}^{2}
          & \qquad \forall g \in \mathcal{G}_{ac}
    \end{align}

.. themed-figure:: gen_limits
   :width: 250
   :alt: Generator limits
   :align: center

   Generator limits

Linear model
~~~~~~~~~~~~

In the linear OPF stack (:doc:`L_models`), only active-power bounds are
enforced. Reactive power and the apparent-power circle are omitted:

.. math::
    :label: eq:gen_L

    P_{g}^{\min} \leq P_{g} \leq P_{g}^{\max}
      \qquad \forall g \in \mathcal{G}_{ac}

Class Reference: :class:`pyflow_acdc.Classes.Gen_AC`

.. autoclass:: pyflow_acdc.Gen_AC
   :no-members:

.. list-table::
   :widths: 20 30 20
   :header-rows: 1

   * - Type
     - Figure for folium plotting
     - Default cost
   * - hydro
     - .. image:: ../images/modelling/icons/hydro.svg
          :width: 100
          :alt: Hydro source icon
          :align: center
     -
   * - nuclear
     - .. image:: ../images/modelling/icons/nuclear.svg
          :width: 100
          :alt: Nuclear source icon
          :align: center
     -
   * - hard coal
     - .. image:: ../images/modelling/icons/coal.svg
          :width: 100
          :alt: Hard Coal source icon
          :align: center
     -
   * - solid biomass
     - .. image:: ../images/modelling/icons/Solid_Biomass.svg
          :width: 100
          :alt: Solid Biomass source icon
          :align: center
     -
   * - geothermal
     - .. image:: ../images/modelling/icons/Geothermal.svg
          :width: 100
          :alt: Geothermal source icon
          :align: center
     -
   * - lignite
     - .. image:: ../images/modelling/icons/Lignite.svg
          :width: 100
          :alt: Lignite source icon
          :align: center
     -
   * - natural gas
     - .. image:: ../images/modelling/icons/Natural_Gas.svg
          :width: 100
          :alt: Natural Gas source icon
          :align: center
     -
   * - oil
     - .. image:: ../images/modelling/icons/Oil.svg
          :width: 100
          :alt: Oil source icon
          :align: center
     -
   * - waste
     - .. image:: ../images/modelling/icons/Waste.svg
          :width: 100
          :alt: Waste source icon
          :align: center
     -
   * - biogas
     - .. image:: ../images/modelling/icons/Biogas.svg
          :width: 100
          :alt: Biogas source icon
          :align: center
     -
   * - ccgt
     - .. image:: ../images/modelling/icons/CCGT.svg
          :width: 100
          :alt: CCGT source icon
          :align: center
     -
   * - diesel
     - .. image:: ../images/modelling/icons/diesel.svg
          :width: 100
          :alt: Diesel source icon
          :align: center
     -
   * - shunt reactor
     - .. image:: ../images/modelling/icons/reactor.svg
          :width: 100
          :alt: Shunt reactor source icon
          :align: center
     -
   * - other
     - .. image:: ../images/modelling/icons/gen.svg
          :width: 100
          :alt: Other source icon
          :align: center
     -



.. _Price_zone_modelling:

Price Zone 
----------



.. themed-figure:: prize_zone_model
   :width: 400
   :alt: Price zone model
   :align: center

   Price zone model

Price zone model is taken from [3]_. The cost of generation quadratic curve is calculated in :doc:`market_coef`.

Class Reference: :class:`pyflow_acdc.Classes.Price_Zone`

.. autoclass:: pyflow_acdc.Price_Zone
   :no-members:

**References**

.. [3] B. C. Valerio, V. A. Lacerda, M. Cheah-Mañe, P. Gebraad, and O. Gomis-Bellmunt,
       "Optimizing offshore wind integration through multi-terminal DC grids: a market-based
       OPF framework for the North Sea interconnectors," IET Conference Proceedings, vol. 2025,
       no. 6, pp. 150–155, 2025. doi: 10.1049/icp.2025.1198