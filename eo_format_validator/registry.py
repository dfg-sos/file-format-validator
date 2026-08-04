import inspect
import importlib
import pkgutil
from types import ModuleType
from typing import Dict, Type, Optional, List, Callable
import logging

from eo_format_validator.model import FileFormatValidator, ValidationRequest

logger = logging.getLogger(__name__)


def import_module(full_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(full_name)
    except Exception as e:
        logger.exception(f"Failed to import module: {full_name}: {e}.")
        return None


class _Registry:
    """Internal registry implementation. Use the module-level ``registry`` instance."""

    def __init__(self):
        self._id_to_validators: Dict[str, Type[FileFormatValidator]] = {}
        self._validators_to_id: Dict[Type[FileFormatValidator], str] = {}

    def load_validators_from_package(
        self,
        pkg_name: str = "eo_format_validator.validators",
        skip_private: bool = True,
    ) -> None:
        """
        Imports all modules found in the given package so that decorators
        (``@registry.register(...)``) are executed and validators auto-register.
        """
        pkg = import_module(pkg_name)
        pkg_path = getattr(pkg, "__path__", None)
        if not pkg_path:
            logger.debug(f"Package {pkg_name} has no __path__ (maybe not a package).")
            return

        for _finder, mod_name, is_pkg in pkgutil.iter_modules(pkg_path):
            if skip_private and mod_name.startswith("_"):
                continue
            if is_pkg:
                continue
            full_name = f"{pkg_name}.{mod_name}"
            import_module(full_name)

    def register(
        self, identifier: str
    ) -> Callable[[Type[FileFormatValidator]], Type[FileFormatValidator]]:
        """Registers a validator class implementation according to the identifier set in the decorator.

        Identifier must not be empty. Registration is case-sensitive, e.g.
        ``'format_1234'`` and ``'Format_1234'`` can be registered separately.
        """
        identifier = identifier.strip()
        if not identifier:
            raise ValueError("Identifier must be non-empty")

        def decorator(cls: Type[FileFormatValidator]) -> Type[FileFormatValidator]:
            if identifier in self._id_to_validators:
                raise KeyError(
                    f"Identifier '{identifier}' already registered for "
                    f"{self._id_to_validators[identifier]}"
                )
            if cls in self._validators_to_id:
                raise KeyError(
                    f"Validator {cls} is already registered under identifier "
                    f"'{self._validators_to_id[cls]}'"
                )
            self._id_to_validators[identifier] = cls
            self._validators_to_id[cls] = identifier
            return cls

        return decorator

    def get_registered_identifiers(self) -> List[str]:
        return sorted(self._id_to_validators.keys())

    def get_identifier_for_validator(
        self, cls: Type[FileFormatValidator]
    ) -> Optional[str]:
        return self._validators_to_id.get(cls)

    def choose_and_instantiate(
        self, request: ValidationRequest
    ) -> Optional[FileFormatValidator]:
        cls = self._id_to_validators.get(request.format_identifier.strip())
        if cls:
            return cls()
        return None


# Module-level singleton instance – imported by validators and consumers alike.
registry = _Registry()
registry.load_validators_from_package("eo_format_validator.validators")
