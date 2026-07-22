"""ITR & Tax Planning — ITR advice, tax optimisation, capital gains, HRA & 80C planner."""
from .._impl import (
    advise_itr,
    optimize_tax_planning,
    generate_capital_gains_calculator,
    generate_hra_80c_planner,
)
__all__ = [
    "advise_itr","optimize_tax_planning",
    "generate_capital_gains_calculator","generate_hra_80c_planner",
]
