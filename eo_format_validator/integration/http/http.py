from typing import Any, List
import requests

from eo_format_validator import EOFormatValidator, ValidationRequestBuilder, ValidationResponseHandler, ValidationResult,ValidationRequest


class HTTPRequestBuilder(ValidationRequestBuilder):
    """Build ValidationRequests from HTTP requests."""
    def __init__(self,request: requests.Request):
        pass

    def build(self) -> ValidationRequest:
        pass


class HTTPResponseHandler(ValidationResponseHandler):
    """Create a validation response from a ValidationResult for an HTTP request."""

    def handle_success(self, validation_result: ValidationResult) -> requests.Response:
        return requests.Response(json=validation_result.to_json(), status=200)

    def handle_failure(self, validation_result: ValidationResult) -> requests.Response:
        return requests.Response(json=validation_result.to_json(), status=400)

    def handle_exception(self, exception: Exception, validation_result: ValidationResult) -> requests.Response:
        return requests.Response(json=validation_result.to_json(), status=500)


class HTTPValidator(EOFormatValidator):
    """EOFormatValidator implementation for HTTP requests."""
    def __init__(self, request: requests.Request):
        super().__init__(HTTPRequestBuilder(request), HTTPResponseHandler())


# def create_app():
#     """Lazy FastAPI app factory.
#     Importing FastAPI is done inside the function so the module can be imported without optional deps.
#     """
#     try:
#         from fastapi import FastAPI
#     except Exception as e:
#         raise RuntimeError("FastAPI is not installed. Install optional dependency 'http' to enable the HTTP adapter.") from e

#     app = FastAPI(title="EO Format Validator")

#     @app.get("/health")
#     def health():
#         return {"status": "ok"}

#     @app.post("/validate")
#     def validate(payload: dict):
#         return {"detail": "HTTP adapter not implemented yet", "received": payload}

#     return app
