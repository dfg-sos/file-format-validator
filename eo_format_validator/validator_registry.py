from typing import Dict, Type, Optional, List, Callable

from eo_format_validator.model.file_format_validator import FileFormatValidator
from eo_format_validator.model.format import Format


class Registry:

    def __init__(self):
        self._id_to_validators: Dict[str, Type[FileFormatValidator]] = {}
        self._validators_to_id: Dict[Type[FileFormatValidator], str] = {}
        #self.failed_validators: Dict[str, str] = {}

    def register(self, identifier: str) -> Callable[[Type[FileFormatValidator]], Type[FileFormatValidator]]:
        """Registers a validator class implementation according to the identifier set in the decorator.
           Identifier must not be empty.
           Registration is case-sensitive, e.g. 'format_1234' and 'Format_1234' can be registered separately."""
        identifier = identifier.strip() #.lower()

        if not identifier:
            raise ValueError("Identifier must be non-empty")

        def decorator(cls: Type[FileFormatValidator]) -> Type[FileFormatValidator]:

            if identifier in self._id_to_validators:
                raise KeyError(f"Identifier '{identifier}' already registered for {self._id_to_validators[identifier]}")

            if cls in self._validators_to_id:
                raise KeyError(f"Validator {cls} is already registered under identifier '{self._validators_to_id[cls]}'")
            self._id_to_validators[identifier] = cls

            self._validators_to_id[cls] = identifier

            return cls
        return decorator

    def get_registered_identifiers(self) -> List[str]:
        return sorted(self._id_to_validators.keys())

    def get_identifier_for_validator(self, cls: Type[FileFormatValidator])-> Optional[str]:
        return self._validators_to_id.get(cls)

    #def get_failed_validators(self) -> Dict[str, str]:
    #    return self.failed_validators

    def choose_and_instantiate(self, file_format: Format) -> Optional[FileFormatValidator]:
        # 1) direct mapping
        #print(file_format)
        cls = self._id_to_validators.get(file_format.get_identifier().strip())
        if cls:
            return cls()
        else:
            return None

        # 2) # Fallback: more advanced checks possible using file (header) to find a validator that supports given file with def choose_validator(self, file_format: Format, file_input: FileInput)

# Singleton
validators = Registry()
