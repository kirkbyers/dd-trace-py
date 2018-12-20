import logging
from wrapt import wrap_function_wrapper as _w

from ...helpers import get_correlation_ids
from ...utils.wrappers import unwrap as _u


def _w_makeRecord(func, instance, args, kwargs):
    record = func(*args, **kwargs)

    # add correlation identifiers to LogRecord
    trace_id, span_id = get_correlation_ids()
    if trace_id and span_id:
        record.trace_id = trace_id
        record.span_id = span_id
    else:
        record.trace_id = 0
        record.span_id = 0

    return record


def patch():
    """
    Patch ``logging`` module in the Python Standard Library for injection of
    tracer information by wrapping the base factory method ``Logger.makeRecord``
    """
    if getattr(logging, '_datadog_patch', False):
        return
    setattr(logging, '_datadog_patch', True)

    _w(logging.Logger, 'makeRecord', _w_makeRecord)


def unpatch():
    if getattr(logging, '_datadog_patch', False):
        setattr(logging, '_datadog_patch', False)

        _u(logging.Logger, 'makeRecord')