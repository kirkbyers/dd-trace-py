import unittest
import logging
import sys
import wrapt

from ddtrace import correlation
from ddtrace import tracer
from ddtrace.compat import StringIO
from ddtrace.utils.logs import patch_logging, unpatch_logging

logger = logging.getLogger()
logger.level = logging.DEBUG


class LoggingTestCase(unittest.TestCase):

    def setUp(self):
        patch_logging()


    def tearDown(self):
        unpatch_logging()


    def test_patch(self):
        """
        Confirm patching was successful
        """
        patch_logging()
        log = logging.getLogger()
        self.assertTrue(isinstance(log.makeRecord, wrapt.BoundFunctionWrapper))


    def test_patch_output(self):
        """
        Check that a log entry from traced function includes correlation
        identifiers in log
        """
        @tracer.wrap()
        def traced_fn():
            log = logging.getLogger()
            log.info('Hello!')
            return correlation.get_correlation_ids()

        def not_traced_fn():
            log = logging.getLogger()
            log.info('Hello!')
            return correlation.get_correlation_ids()

        def run_fn(fn):
            out = StringIO()
            sh = logging.StreamHandler(out)

            try:
                fmt = '%(asctime)-15s %(name)-5s %(levelname)-8s dd.trace_id=%(trace_id)s dd.span_id=%(span_id)s %(message)s'
                sh.setFormatter(logging.Formatter(fmt))
                logger.addHandler(sh)
                correlation_ids = fn()
            finally:
                logger.removeHandler(sh)

            return out.getvalue().strip(), correlation_ids


        # with logging patched
        traced_fn_output, traced_ids = run_fn(traced_fn)
        self.assertTrue('dd.trace_id={}'.format(traced_ids[0]) in traced_fn_output)
        self.assertTrue('dd.span_id={}'.format(traced_ids[1]) in traced_fn_output)

        not_traced_fn_output, not_traced_ids = run_fn(not_traced_fn)
        self.assertIsNone(not_traced_ids[0])
        self.assertIsNone(not_traced_ids[1])
        self.assertTrue('dd.trace_id= dd.span_id= Hello!' in not_traced_fn_output)

        # logging without patching
        unpatch_logging()
        traced_fn_output, _ = run_fn(traced_fn)
        self.assertFalse('dd.trace_id=' in traced_fn_output)
        self.assertFalse('dd.span_id=' in traced_fn_output)

