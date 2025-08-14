"""Helper package that exposes core financial calculators.

The `calculators` package contains small, focused modules that each implement
specific pieces of the retirement planning logic:

* ``taxes`` – progressive federal and state tax calculations including capital gains.
* ``rmd`` – Required Minimum Distribution rules and Uniform Lifetime table.
* ``social_security`` – simplified Social Security benefit estimation based on PIA and claiming age.
* ``monte_carlo`` – engine for simulating investment returns, withdrawals and success probability.
* ``roth`` – functions for modelling Roth conversions and exploring different strategies.

Each module exposes a few public functions with clear parameters and returns.  See
individual docstrings for details.
"""

from . import taxes, rmd, social_security, monte_carlo, roth  # noqa: F401

__all__ = ["taxes", "rmd", "social_security", "monte_carlo", "roth"]