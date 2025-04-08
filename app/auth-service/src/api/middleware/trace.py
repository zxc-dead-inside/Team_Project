from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.context import attach, detach
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request


class TraceParentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        context = extract(request.headers)
        token = attach(context)

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("incoming-request"):
            response = await call_next(request)

        detach(token)
        return response
