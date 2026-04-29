import inspect
import importlib
import pkgutil
from types import ModuleType
from typing import Dict, Type, Optional, List, Callable
import logging
import inspect
from eo_format_validator.model import FileFormatValidator, Format

logger = logging.getLogger(__name__)

def import_module(full_name: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(full_name)
    except Exception as e:
        logger.exception(f"Failed to import module: {full_name}: {e}.")
        return None

class Registry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Registry, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._id_to_validators: Dict[str, Type[FileFormatValidator]] = {}
        self._validators_to_id: Dict[Type[FileFormatValidator], str] = {}
        Registry.load_validators_from_package("eo_format_validator.validators")
    
    @staticmethod
    def load_validators_from_package(pkg_name: str = "eo_format_validator.validators",
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
        pkg = import_module(pkg_name)
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
            mod = import_module(full_name)
            if mod is None:
                continue
            # optional: auto register validator classes found

    @staticmethod
    def register(identifier: str) -> Callable[[Type[FileFormatValidator]], Type[FileFormatValidator]]:
        """Registers a validator class implementation according to the identifier set in the decorator.
           Identifier must not be empty.
           Registration is case-sensitive, e.g. 'format_1234' and 'Format_1234' can be registered separately."""
        identifier = identifier.strip() #.lower()
        registrySingleton = Registry._instance

        if not identifier:
            raise ValueError("Identifier must be non-empty")

        def decorator(cls: Type[FileFormatValidator]) -> Type[FileFormatValidator]:

            if identifier in registrySingleton._id_to_validators:
                raise KeyError(f"Identifier '{identifier}' already registered for {registrySingleton._id_to_validators[identifier]}")

            if cls in registrySingleton._validators_to_id:
                raise KeyError(f"Validator {cls} is already registered under identifier '{registrySingleton._validators_to_id[cls]}'")
            registrySingleton._id_to_validators[identifier] = cls

            registrySingleton._validators_to_id[cls] = identifier

            return cls
        return decorator

    def get_registered_identifiers(self) -> List[str]:
        return sorted(self._id_to_validators.keys())

    def get_identifier_for_validator(self, cls: Type[FileFormatValidator])-> Optional[str]:
        return self._validators_to_id.get(cls)

    def choose_and_instantiate(self, file_format: Format) -> Optional[FileFormatValidator]:
        cls = self._id_to_validators.get(file_format.get_identifier().strip())
        if cls:
            return cls()
        else:
            return None