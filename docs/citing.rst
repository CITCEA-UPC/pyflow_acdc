Citing pyflow-acdc
==================

If you use **pyflow-acdc** in your work, please cite the publication that
matches the feature you relied on. Software citation metadata is also in
``CITATION.cff`` (GitHub *Cite this repository*).

The short forms below match the README. BibTeX follows each entry.

General framework
-----------------

Use for general usage of the package / AC–DC OPF tool.

B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
"An Optimal Power Flow Tool for AC/DC Systems, Applied to the Analysis of the
North Sea Grid for Offshore Wind Integration," in *IEEE Transactions on Power
Systems*, vol. 40, no. 5, pp. 4278–4291, Sept. 2025,
doi: `10.1109/TPWRS.2025.3533889 <https://doi.org/10.1109/TPWRS.2025.3533889>`_.

.. code-block:: bibtex

    @ARTICLE{bcv2025opf,
      author  = {Valerio, Bernardo Castro and Lacerda, Vinicius A. and
                 Cheah-Mane, Marc and Gebraad, Pieter and Gomis-Bellmunt, Oriol},
      journal = {IEEE Transactions on Power Systems},
      title   = {An Optimal Power Flow Tool for AC/DC Systems, Applied to the
                 Analysis of the North Sea Grid for Offshore Wind Integration},
      year    = {2025},
      volume  = {40},
      number  = {5},
      pages   = {4278--4291},
      doi     = {10.1109/TPWRS.2025.3533889}
    }

Market-based OPF
----------------

Use for market / price-zone integration into OPF.

B. C. Valerio, V. A. Lacerda, M. Cheah-Mane, P. Gebraad and O. Gomis-Bellmunt,
"Optimizing Offshore Wind Integration through Multi-Terminal DC Grids: A
Market-Based OPF Framework for the North Sea Interconnectors,"
*IET Conference Proceedings*, vol. 2025, no. 6, pp. 150–155, 2025,
doi: `10.1049/icp.2025.1198 <https://doi.org/10.1049/icp.2025.1198>`_.

.. code-block:: bibtex

    @ARTICLE{bcv2025market,
      author  = {Valerio, Bernardo Castro and Lacerda, Vinicius A. and
                 Cheah-Mane, Marc and Gebraad, Pieter and Gomis-Bellmunt, Oriol},
      title   = {Optimizing Offshore Wind Integration through Multi-Terminal DC
                 Grids: A Market-Based OPF Framework for the North Sea
                 Interconnectors},
      journal = {IET Conference Proceedings},
      year    = {2025},
      volume  = {2025},
      number  = {6},
      pages   = {150--155},
      doi     = {10.1049/icp.2025.1198}
    }

Transmission expansion planning
--------------------------------

Use for hybrid AC/DC TEP / MINLP expansion workflows.

B. C. Valerio, M. Cheah-Mane, V. A. Lacerda, P. Gebraad and O. Gomis-Bellmunt,
"Transmission expansion planning for hybrid AC/DC grids using a mixed-integer
non-linear programming approach," *International Journal of Electrical Power &
Energy Systems*, vol. 174, p. 111459, 2026,
doi: `10.1016/j.ijepes.2025.111459 <https://doi.org/10.1016/j.ijepes.2025.111459>`_.

.. code-block:: bibtex

    @article{VALERIO2026111459,
      author  = {Bernardo Castro Valerio and Marc Cheah-Mane and
                 Vinicius A. Lacerda and Pieter Gebraad and Oriol Gomis-Bellmunt},
      title   = {Transmission expansion planning for hybrid AC/DC grids using a
                 mixed-integer non-linear programming approach},
      journal = {International Journal of Electrical Power \& Energy Systems},
      volume  = {174},
      pages   = {111459},
      year    = {2026},
      issn    = {0142-0615},
      doi     = {10.1016/j.ijepes.2025.111459},
      url     = {https://www.sciencedirect.com/science/article/pii/S0142061525010075}
    }

Array optimization
------------------

Use for wind-park inter-array cabling / CSS / array sizing.

Castro Valerio, B., Gebraad, P. M. O., Cheah-Mane, M., A. Lacerda, V., and
Gomis-Bellmunt, O.: A multi-stage methodology for wind park inter-array
cabling: graph preparation, layout, and sizing, *Wind Energ. Sci. Discuss.*
[preprint], https://doi.org/10.5194/wes-2026-53, in review, 2026.

.. code-block:: bibtex

    @Article{wes-2026-53,
      author  = {Castro Valerio, B. and Gebraad, P. M. O. and Cheah-Mane, M. and
                 A. Lacerda, V. and Gomis-Bellmunt, O.},
      title   = {A multi-stage methodology for wind park inter-array cabling:
                 graph preparation, layout, and sizing},
      journal = {Wind Energy Science Discussions},
      year    = {2026},
      note    = {preprint, in review},
      doi     = {10.5194/wes-2026-53},
      url     = {https://doi.org/10.5194/wes-2026-53}
    }

BESS / hydrogen / energy-island operation
-----------------------------------------

Use when citing :class:`~pyflow_acdc.Storage`,
:func:`~pyflow_acdc.add_storage`, :class:`~pyflow_acdc.Electrolyser`,
:func:`~pyflow_acdc.add_electrolyser`, or
:func:`~pyflow_acdc.window_nl_opf` / rolling window operation.

M. Useche-Arteaga, P. Gebraad, V. Lacerda, M. Cheah-Mane, and O. Gomis-Bellmunt,
*Optimizing the operation of energy islands with predictive nonlinear
programming -- a case study based on the Princess Elisabeth Energy Island*,
*Wind Energy Science*, 11(2), 349–372, 2026,
doi: `10.5194/wes-11-349-2026 <https://doi.org/10.5194/wes-11-349-2026>`_.

Modelling notes: :doc:`api/modelling_flexible_assets` (BESS §3.3, electrolyser
§3.4). Coupled window / rolling: :doc:`api/window` (API),
:doc:`usage_window_opf` (workflow).

.. code-block:: bibtex

    @Article{wes-11-349-2026,
      author  = {Useche-Arteaga, M. and Gebraad, P. and Lacerda, V. and
                 Cheah-Mane, M. and Gomis-Bellmunt, O.},
      title   = {Optimizing the operation of energy islands with predictive
                 nonlinear programming -- a case study based on the
                 {Princess Elisabeth Energy Island}},
      journal = {Wind Energy Science},
      volume  = {11},
      year    = {2026},
      number  = {2},
      pages   = {349--372},
      url     = {https://wes.copernicus.org/articles/11/349/2026/},
      doi     = {10.5194/wes-11-349-2026}
    }

For controllable heat pumps / LEC flexibility:

If you use :class:`~pyflow_acdc.HeatPump` or
:func:`~pyflow_acdc.add_heat_pump`, please also cite:

M. Montalà-Palau, J. J. Markus, M. Kazemi, M. Cheah-Mañé, C. Papadimitriou,
and O. Gomis-Bellmunt, *Enhancing Distribution System Resilience through Energy
Communities*, CIRED 2026 Brussels Workshop, Paper 1361, 2026.

Modelling: :doc:`api/modelling_flexible_assets` (heat-pump section).

Sparse SOCP / AC–DC energy hubs
--------------------------------

Use when citing :func:`~pyflow_acdc.socp_optimise` /
:func:`~pyflow_acdc.soc_window_optimisation` (``[SOCP]`` extra).

M. Useche-Arteaga, W. Gil-González, P. Gebraad, M. Cheah-Mane, V. Lacerda, and
O. Gomis-Bellmunt, *Efficient AC/DC energy hubs operation using sparse SOCP
relaxation and chance-constrained optimization*, *Sustainable Energy, Grids and
Networks*, 46, 102217, 2026,
doi: `10.1016/j.segan.2026.102217 <https://doi.org/10.1016/j.segan.2026.102217>`_.

Plan: ``plans/convex_acdc_socp_plan.md``.

.. code-block:: bibtex

    @article{USECHEARTEAGA2026102217,
      author  = {Useche-Arteaga, M. and Gil-González, W. and Gebraad, P. and
                 Cheah-Mane, M. and Lacerda, V. and Gomis-Bellmunt, O.},
      title   = {Efficient AC/DC energy hubs operation using sparse SOCP
                 relaxation and chance-constrained optimization},
      journal = {Sustainable Energy, Grids and Networks},
      volume  = {46},
      pages   = {102217},
      year    = {2026},
      doi     = {10.1016/j.segan.2026.102217}
    }
