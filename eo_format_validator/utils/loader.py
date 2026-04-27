import pkgutil
import importlib
import logging
import inspect
from types import ModuleType
from typing import Optional

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.validator_registry import validators

logger = logging.getLogger(__name__)

def _import_module(full_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(full_name)
    except Exception as e:
        logger.exception(f"Failed to import module: {full_name}: {e}.")
        return None

def _auto_register_validators_in_module(mod: ModuleType):
    """Optional fallback: automatic registration of validators to avoid missing decorator registration."""
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        # Ignore classes not defined in this module to avoid registering imports
        if obj.__module__ != mod.__name__:
            continue
        if issubclass(obj, FileFormatValidator) and obj is not FileFormatValidator:
            # validators.register overrides multiple registration
            try:
                validators.register(obj)
                logger.debug(f"Auto-registered validator '{name}' from module '{mod.__name__}'.")
            except Exception:
                logger.exception(f"Failed to register validator '{name}' from module '{mod.__name__}'.")

def load_validators_from_package(pkg_name: str = "eo_format_validator.validators",
                                recursive: bool = True,
                                auto_register: bool = True,
                                skip_private: bool = True) -> None:
    """
    Imports all modules found in given package.
    Optionally auto-registers validators to avoid missing decorator registration.

    - package_name: full name of the package to inspect
    - recursive: flag if sub-packages also should be inspected
    - auto_register: flag if auto-registration fallback is activated
    - skip_private: flag if private modules should be skipped
    """

    # 1) Import the package
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        logger.exception(f"Could not import package {pkg_name}.")
        return

    # 2) Search for the package path
    pkg_path = getattr(pkg, "__path__", None)
    if not pkg_path:
        logger.debug(f"Package {pkg_name} has no __path__ (maybe not a package)." )
        return

    # 3) Iterate all modules within the package
    for finder, mod_name, is_pkg in pkgutil.iter_modules(pkg_path):
        #print(f"TEST: module found: {mod_name}")
        if skip_private and mod_name.startswith("_"):
            continue
        full_name = f"{pkg_name}.{mod_name}"
        mod = _import_module(full_name)
        if mod is None:
            continue
        # optional: auto register validator classes found
        if auto_register:
            _auto_register_validators_in_module(mod)

        # 4) Recursive inspection of sub-packages if flag is set, only works for packages!
        if recursive and is_pkg:
            load_validators_from_package(full_name, recursive=recursive, auto_register=auto_register, skip_private=skip_private)
