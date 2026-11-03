import inspect
import importlib
import importlib.metadata
import pkgutil
from types import ModuleType
from typing import Dict, Type, Optional, List, Callable
import logging

from format_validator.model import FileFormatValidator, FormatIdentifier

logger = logging.getLogger(__name__)

PLUGIN_ENTRY_POINT_GROUP = "format_validator.validators"


class DuplicateRegistrationError(KeyError):
    """An identifier or validator class is registered twice."""


def import_module(full_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(full_name)
    except Exception as e:
        logger.exception(f"Failed to import module: {full_name}: {e}.")
        return None


class _Registry:
    """Internal registry implementation. Use the module-level ``registry`` instance."""

    def __init__(self):
        self._id_to_validators: Dict[FormatIdentifier, Type[FileFormatValidator]] = {}
        self._validators_to_id: Dict[Type[FileFormatValidator], FormatIdentifier] = {}

    def load_validators_from_package(
        self,
        pkg_name: str,
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

    def load_plugins(self, group: str = PLUGIN_ENTRY_POINT_GROUP) -> List[str]:
        """
        Imports every module registered under the entry-point ``group`` so that
        validators shipped by other packages auto-register. A package declares
        its validators in its ``pyproject.toml``::

            [project.entry-points."format_validator.validators"]
            bio = "format_validator_bio.validators"

        A plugin that fails to import is logged and skipped. A plugin that
        registers an identifier or class that is already taken raises a
        ``DuplicateRegistrationError``.

        Returns the names of the entry points that were loaded.
        """
        loaded = []
        for ep in importlib.metadata.entry_points(group=group):
            try:
                ep.load()
            except DuplicateRegistrationError:
                raise
            except Exception as e:
                logger.exception(f"Failed to load validator plugin '{ep.name}' ({ep.value}): {e}.")
                continue
            logger.info(f"Loaded validator plugin '{ep.name}' ({ep.value}).")
            loaded.append(ep.name)
        return loaded

    def register(
        self, *identifiers: str | FormatIdentifier
    ) -> Callable[[Type[FileFormatValidator]], Type[FileFormatValidator]]:
        """Registers a validator class implementation according to the identifiers set in the decorator.

        Several identifiers register one class for formats that the file cannot tell apart, e.g.
        GeoTIFF and DEM. The first one is the validator's own identifier, see
        ``get_identifier_for_validator``. Identifiers must not be empty. Registration is
        case-sensitive, e.g. ``'format_1234'`` and ``'Format_1234'`` can be registered separately.
        """
        if not identifiers:
            raise ValueError("At least one identifier is required")
        ids = [self._to_identifier(identifier) for identifier in identifiers]

        def decorator(cls: Type[FileFormatValidator]) -> Type[FileFormatValidator]:
            for identifier in ids:
                if identifier in self._id_to_validators:
                    raise DuplicateRegistrationError(
                        f"Identifier '{identifier}' already registered for "
                        f"{self._id_to_validators[identifier]}"
                    )
            if cls in self._validators_to_id:
                raise DuplicateRegistrationError(
                    f"Validator {cls} is already registered under identifier "
                    f"'{self._validators_to_id[cls]}'"
                )
            for identifier in ids:
                self._id_to_validators[identifier] = cls
            self._validators_to_id[cls] = ids[0]
            return cls

        return decorator

    @staticmethod
    def _to_identifier(identifier: str | FormatIdentifier) -> FormatIdentifier:
        if isinstance(identifier, FormatIdentifier):
            return identifier
        stripped = identifier.strip()
        if not stripped:
            raise ValueError("Identifier must be non-empty")
        return FormatIdentifier(stripped)

    def get_registered_identifiers(self) -> List[FormatIdentifier]:
        return sorted(self._id_to_validators.keys(), key=lambda fi: fi.id)

    def get_identifier_for_validator(
        self, cls: Type[FileFormatValidator]
    ) -> Optional[FormatIdentifier]:
        return self._validators_to_id.get(cls)

    def get_validator_class(
        self, identifier: FormatIdentifier
    ) -> Optional[Type[FileFormatValidator]]:
        return self._id_to_validators.get(identifier)


# Module-level singleton instance – imported by validators and consumers alike.
registry = _Registry()
