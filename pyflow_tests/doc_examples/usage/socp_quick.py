import pyflow_acdc as pyf

grid, _ = pyf.cases["case39_acdc"]()

problem, variables, timing, stats = pyf.socp_optimise(
    grid,
    build_only=True,
)

print(problem.status)
print(stats["n_vars"], stats["n_constr"], timing["build"])
