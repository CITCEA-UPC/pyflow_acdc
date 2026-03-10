import os
from contextlib import contextmanager


def quick_fake_enabled():
    return os.getenv("PYFLOW_QUICK_FAKE_SOLVE", "").strip() == "1"


def _fake_pyomo_solve(*args, **kwargs):
    return None, {
        "solution_found": False,
        "termination_condition": "unknown",
        "solver_message": "mocked quick-mode solve",
        "time": 0.0,
    }


@contextmanager
def quick_fake_solve_context(opf=False, tep=False):
    patched = []
    try:
        if opf:
            import pyflow_acdc.ACDC_OPF as acdc_opf

            old = acdc_opf.pyomo_model_solve
            acdc_opf.pyomo_model_solve = _fake_pyomo_solve
            patched.append((acdc_opf, old))
        if tep:
            import pyflow_acdc.ACDC_Static_TEP as static_tep

            old = static_tep.pyomo_model_solve
            static_tep.pyomo_model_solve = _fake_pyomo_solve
            patched.append((static_tep, old))
        yield
    finally:
        for module, old in reversed(patched):
            module.pyomo_model_solve = old
