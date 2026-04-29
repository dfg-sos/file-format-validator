from abc import ABC, abstractmethod
from typing import Any, List

from .validation_request import ValidationRequest


class ValidationRequestBuilder(ABC):
    """
       Abstract builder interface for creating ValidationRequests from different input sources.
       For each client (cwltool, HTTP, CLI), implement their own builder.
           Returns:
               List of ValidationRequests
    """

    @abstractmethod
    def build(self) -> ValidationRequest:
        """
           Build a ValidationRequest from a client-specific source.

               Args:
                   No args.
                   Source data is set separately in classes at initialization: client input data (dict, object, JSON, etc.)

               Returns:
                   ValidationRequest ready for validation

               Raises:
                   BuilderException: If request cannot be built
        """
        pass

