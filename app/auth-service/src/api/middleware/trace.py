import random

from fastapi import Request
from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.trace import set_span_in_context, SpanContext, TraceFlags
from starlette.middleware.base import BaseHTTPMiddleware


class TraceParentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = None

        if "traceparent" not in request.headers:
            new_trace_id = random.getrandbits(128)
            new_span_id = random.getrandbits(64)

            span_context = SpanContext(
                trace_id=new_trace_id,
                span_id=new_span_id,
                is_remote=False,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
                trace_state={}
            )
            span = trace.NonRecordingSpan(span_context)

            context = set_span_in_context(span)
            token = attach(context)

        response = await call_next(request)

        if token:
            detach(token)

        return response
