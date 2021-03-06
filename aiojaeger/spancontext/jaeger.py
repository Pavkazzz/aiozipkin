from typing import Optional, Tuple

from aiojaeger.mypy_types import Headers
from aiojaeger.spancontext import BaseTraceContext
from aiojaeger.version import __version__


class JaegerConst:
    # Max number of bits allowed to use when generating Trace ID
    _max_trace_id_bits = 128

    # Max number of bits to use when generating random ID
    _max_id_bits = 64

    # How often remotely controlled sampler polls for sampling strategy
    DEFAULT_SAMPLING_INTERVAL = 60

    # How often remote reporter does a preemptive flush of its buffers
    DEFAULT_FLUSH_INTERVAL = 1

    # Name of the HTTP header used to encode trace ID
    TRACE_ID_HEADER = "uber-trace-id"

    # Prefix for HTTP headers used to record baggage items
    BAGGAGE_HEADER_PREFIX = "uberctx-"

    # The name of HTTP header or a TextMap carrier key which, if found in the
    # carrier, forces the trace to be sampled as "debug" trace. The value of
    # the header is recorded as the tag on the # root span, so that the trace
    # can be found in the UI using this value as a correlation ID.
    DEBUG_ID_HEADER_KEY = "jaeger-debug-id"

    # The name of HTTP header or a TextMap carrier key that can be used to
    # pass additional baggage to the span, e.g. when executing an ad-hoc
    # curl request: curl -H 'jaeger-baggage: k1=v1,k2=v2' http://...
    BAGGAGE_HEADER_KEY = "jaeger-baggage"

    JAEGER_CLIENT_VERSION = f"aiojaeger-{__version__}"

    # Tracer-scoped tag that tells the version of Jaeger client library
    JAEGER_VERSION_TAG_KEY = "jaeger.version"

    # Tracer-scoped tag that contains the hostname
    JAEGER_HOSTNAME_TAG_KEY = "hostname"

    # Tracer-scoped tag that is used to report ip of the process.
    JAEGER_IP_TAG_KEY = "ip"

    # the type of sampler that always makes the same decision.
    SAMPLER_TYPE_CONST = "const"

    # the type of sampler that polls Jaeger agent for sampling strategy.
    SAMPLER_TYPE_REMOTE = "remote"

    # the type of sampler that samples traces with a certain fixed probability.
    SAMPLER_TYPE_PROBABILISTIC = "probabilistic"

    # the type of sampler that samples only up to a fixed number
    # of traces per second.
    # noinspection SpellCheckingInspection
    SAMPLER_TYPE_RATE_LIMITING = "ratelimiting"

    # the type of sampler that samples only up to a fixed number
    # of traces per second.
    # noinspection SpellCheckingInspection
    SAMPLER_TYPE_LOWER_BOUND = "lowerbound"

    # Tag key for unique client identifier. Used in throttler implementation.
    CLIENT_UUID_TAG_KEY = "client-uuid"

    # max length for tag values. Longer values will be truncated.
    MAX_TAG_VALUE_LENGTH = 1024

    # max length for traceback data. Longer values will be truncated.
    MAX_TRACEBACK_LENGTH = 4096

    # Constant for sampled flag
    SAMPLED_FLAG = 0x01

    # Constant for debug flag
    DEBUG_FLAG = 0x02

    # How often throttler polls for credits
    DEFAULT_THROTTLER_REFRESH_INTERVAL = 5

    @classmethod
    def make_trace_id(cls, c: BaseTraceContext) -> str:
        # https://www.jaegertracing.io/docs/1.17/client-libraries/#key
        flags = 0
        if c.debug:
            flags |= cls.DEBUG_FLAG
        if c.sampled:
            flags |= cls.SAMPLED_FLAG
        return f"{c.trace_id}:{c.span_id}:{c.parent_id}:{flags}"

    @classmethod
    def parse_trace_id(cls, header_trace_id: str) -> Tuple[int, ...]:
        try:
            parts = header_trace_id.split(":", 4)
        except AttributeError:
            raise ValueError
        if len(parts) != 4:
            raise ValueError

        def to_int(s: str) -> int:
            return int(s, 16)

        trace_id, span_id, parent_id, flags = tuple(map(to_int, parts))
        if trace_id <= 0 or span_id <= 0:
            raise ValueError
        if parent_id < 0 or flags < 0:
            raise ValueError
        return trace_id, span_id, parent_id, flags

    @classmethod
    def make_headers(cls, context: BaseTraceContext) -> Headers:
        """
        Creates dict with jaeger headers from supplied trace context.
        """

        # TODO: baggage keys
        headers = {
            cls.TRACE_ID_HEADER: cls.make_trace_id(context),
        }
        return headers

    @classmethod
    def make_context(cls, headers: Headers) -> Optional[BaseTraceContext]:
        # TODO: add validation for trace_id/span_id/parent_id

        headers = {k.lower(): v for k, v in headers.items()}

        try:
            # TODO: flags. debug and sampled
            trace_id, span_id, parent_id, flags = cls.parse_trace_id(
                headers[cls.TRACE_ID_HEADER]
            )
        except (ValueError, KeyError):
            return None

        return JaegerTraceContext(
            trace_id=trace_id,
            parent_id=parent_id,
            span_id=span_id,
            sampled=bool(flags & cls.SAMPLED_FLAG),
            debug=bool(flags & cls.DEBUG_FLAG),
            shared=False,
        )


class JaegerTraceContext(BaseTraceContext):
    @classmethod
    def make_context(cls, headers: Headers) -> Optional[BaseTraceContext]:
        return JaegerConst.make_context(headers)

    def make_headers(self) -> Headers:
        return JaegerConst.make_headers(self)
