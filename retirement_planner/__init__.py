"""Compatibility namespace for legacy imports.

This project originally exposed its calculator modules under a
`retirement_planner` package.  The tests – and likely third-party code – still
expect to import modules such as ``retirement_planner.calculators``.  During a
refactor the top-level package was renamed, leaving these imports broken.

To preserve backwards compatibility we lazily import the existing
``calculators`` package and register it under the ``retirement_planner``
namespace.  This mirrors the original module layout without requiring us to
duplicate code or move files around.
"""

from importlib import import_module
import sys

# Expose ``retirement_planner.calculators`` as an alias to the real
# ``calculators`` package.
_calculators = import_module("calculators")
sys.modules[__name__ + ".calculators"] = _calculators
