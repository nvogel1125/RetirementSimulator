"""Core package for the retirement planner.

This package bundles the financial calculators and Streamlit components used
throughout the application.  Subpackages are exposed for convenience so they
can be imported directly from :mod:`retirement_planner`.
"""

from . import calculators, components

__all__ = ["calculators", "components"]
