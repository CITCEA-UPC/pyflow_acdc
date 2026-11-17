.. _ACDC_converter_modelling:

AC/DC Converter
===============

.. themed-figure:: assymetrical
   :width: 400
   :alt: Asymmetrical monopolar converter configuration
   :align: center

   Asymmetrical monopolar converter configuration

.. themed-figure:: symetrical
   :width: 400
   :alt: Symmetrical monopolar converter configuration
   :align: center

   Symmetrical monopolar converter configuration

.. themed-figure:: bipolar_exp
   :width: 400
   :alt: Bipolar converter configuration
   :align: center

   Bipolar converter configuration

.. themed-figure:: converter_model
   :width: 400
   :alt: Equivalent converter model
   :align: center

   Equivalent converter model

Equivalent converter model is taken from [1]_.

Non-linear model
----------------

.. math::
    :label: eq:PsQs

    \begin{align}
    P_s &= -V_i^2 G_{tf}+ V_iV_f[G_{tf} \cos(\theta_i-\theta_f)+B_{tf} \sin(\theta_i-\theta_f)] \\
    Q_s &= V_i^2 B_{tf}+ V_iV_f[G_{tf} \sin(\theta_i-\theta_f)-B_{tf} \cos(\theta_i-\theta_f)]
    \end{align}

.. math::
    :label: eq:PcQc

    \begin{align}
    P_c &= V_c^2 G_{pr}- V_fV_c[G_{pr} \cos(\theta_f-\theta_c)-B_{pr} \sin(\theta_f-\theta_c)] \\
    Q_c &= -V_c^2 B_{pr}+ V_fV_c[G_{pr} \sin(\theta_f-\theta_c)+B_{pr} \cos(\theta_f-\theta_c)]
    \end{align}

.. math::
    :label: eq:F1F2

    \begin{align}
    P_{cf}-P_{sf} &= 0 \\
    Q_{cf}-Q_{sf}-Q_f &= 0
    \end{align}

.. math::
    :label: eq:powerelec

    P_{c_{AC}} + P_{cn_{loss}} + P_{cn_{DC}} = 0

.. math::
    :label: eq:PLoss

    P_{cn_{loss}} = a\cdot p_{cn} +b \frac{\sqrt{P_{c_{AC}}^2+Q_{c_{AC}}^2}}{V_{c_{AC}}} + \frac{c}{p_{cn}} \left( \frac{P_{c_{AC}}^2+Q_{c_{AC}}^2} {V_{c_{AC}}^2} \right)

.. math::
    :label: eq:pol_conv

    p_{cn} = \begin{cases}
        1, & \text{for asymmetrical or symmetrical monopolar} \\
        2, & \text{for bipolar}
    \end{cases}

.. math::
    :label: eq:ConvLim

    \begin{align}
        P_{s_{AC}}^2+Q_{s_{AC}}^2 &\leq S_{cn_{rating}}^2 \qquad \forall cn \in \mathcal{C}n \\
        |P_{cn_{DC}}| &\leq S_{cn_{rating}}  \qquad \forall cn \in \mathcal{C}n
    \end{align}

Linear model
------------

In the linear OPF stack (:doc:`L_models`), converters use an active-power link
with affine losses in :math:`P_s`:

.. math::
    :label: eq:Conv_L

    \begin{align}
        p_{cn}\, P_{s}
        + P_{cn_{DC}}
        + p_{cn}\,(a_{conv}+b_{conv} P_{s})
        &= 0 \\
        |P_{s}| &\leq S_{cn_{rating}}
          \qquad \forall cn \in \mathcal{C}n
    \end{align}

SOCP model
----------

In the sparse SOCP stack (:doc:`socp`), converters use AC-side apparent power
:math:`S_s`, DC injection, and an affine loss epigraph in :math:`|\Re(S_s)|`:

.. math::
    :label: eq:Conv_SOCP

    \begin{align}
        \Re(S_{s}) + P_{cn_{DC}} + P_{cn_{loss}} &= 0 \\
        t &\geq |\Re(S_{s})| \\
        P_{cn_{loss}} &= a_{conv} + b_{conv}\, t \\
        \|S_{s}\| &\leq S_{cn_{rating}}
          \qquad \forall cn \in \mathcal{C}n
    \end{align}

Class Reference: :class:`pyflow_acdc.Classes.AC_DC_converter`

.. autoclass:: pyflow_acdc.AC_DC_converter
   :no-members:

**References**

.. [1] B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
       "An optimal power flow tool for AC/DC systems, applied to the analysis of the
       North Sea Grid for offshore wind integration" in IEEE Transactions on Power
       Systems, doi: 10.1109/TPWRS.2023.3533889.

