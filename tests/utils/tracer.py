from ddtrace.encoding import JSONEncoder, MsgpackEncoder
from ddtrace.tracer import Tracer
from ddtrace.writer import AgentWriter


class DummyWriter(AgentWriter):
    """DummyWriter is a small fake writer used for tests. not thread-safe."""

    def __init__(self, *args, **kwargs):
        # original call
        super(DummyWriter, self).__init__(*args, **kwargs)

        # dummy components
        self.spans = []
        self.traces = []
        self.services = {}
        self.json_encoder = JSONEncoder()
        self.msgpack_encoder = MsgpackEncoder()

    def write(self, spans=None, services=None):
        if spans:
            # the traces encoding expect a list of traces so we
            # put spans in a list like we do in the real execution path
            # with both encoders
            trace = [spans]
            self.json_encoder.encode_traces(trace)
            self.msgpack_encoder.encode_traces(trace)
            self.spans += spans
            self.traces += trace

        if services:
            self.json_encoder.encode_services(services)
            self.msgpack_encoder.encode_services(services)
            self.services.update(services)

    def pop(self):
        # dummy method
        s = self.spans
        self.spans = []
        return s

    def pop_traces(self):
        # dummy method
        traces = self.traces
        self.traces = []
        return traces

    def pop_services(self):
        # dummy method
        s = self.services
        self.services = {}
        return s


class DummyTracer(Tracer):
    """
    DummyTracer is a tracer which uses the DummyWriter by default
    """
    def __init__(self, *args, **kwargs):
        super(DummyTracer, self).__init__(*args, **kwargs)
        self._update_writer()

    def _update_writer(self):
        self.writer = DummyWriter(
                hostname=self.writer.api.hostname,
                port=self.writer.api.port,
                filters=self.writer._filters,
                priority_sampler=self.writer._priority_sampler,
        )

    def configure(self, *args, **kwargs):
        super(DummyTracer, self).configure(*args, **kwargs)
        # `.configure()` may reset the writer
        self._update_writer()
