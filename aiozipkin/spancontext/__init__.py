# possible span kinds
import abc

from pydantic import BaseModel

from aiozipkin.mypy_types import Headers, OptBool, OptStr

CLIENT = "CLIENT"
SERVER = "SERVER"
PRODUCER = "PRODUCER"
CONSUMER = "CONSUMER"


class BaseTraceContext(BaseModel):
    """Immutable class with trace related data that travels across
    process boundaries.
    """

    trace_id: str
    span_id: str
    parent_id: OptStr
    sampled: OptBool
    debug: bool
    shared: bool

    @classmethod
    @abc.abstractmethod
    def make_headers(cls) -> Headers:
        """Creates dict with zipkin headers from available context.

        Resulting dict should be passed to HTTP client  propagate contest
        to other services.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def make_context(cls, headers: Headers):
        pass


class DummyTraceContext(BaseTraceContext):
    @classmethod
    def make_headers(cls) -> Headers:
        return {}

    @classmethod
    def make_context(cls, headers: Headers, sampled=True):
        return cls(
            trace_id="dummy-trace-id",
            span_id="dummy-span-id",
            parent_id="dummy-parent-id",
            debug=False,
            sampled=sampled,
            shared=False,
        )