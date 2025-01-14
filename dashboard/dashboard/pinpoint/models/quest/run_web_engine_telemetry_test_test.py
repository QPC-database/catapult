# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest

from dashboard.pinpoint.models.quest import run_web_engine_telemetry_test
from dashboard.pinpoint.models.quest import run_performance_test
from dashboard.pinpoint.models.quest import run_telemetry_test
from dashboard.pinpoint.models.quest import run_test_test

_BASE_ARGUMENTS = {
    'configuration': 'some_configuration',
    'swarming_server': 'server',
    'dimensions': run_test_test.DIMENSIONS,
    'benchmark': 'some_benchmark',
    'browser': 'web-engine-shell',
    'builder': 'builder name',
    'target': 'performance_web_engine_test_suite',
}
_COMBINED_DEFAULT_EXTRA_ARGS = (
    run_telemetry_test._DEFAULT_EXTRA_ARGS +
    run_performance_test._DEFAULT_EXTRA_ARGS +
    run_web_engine_telemetry_test._DEFAULT_EXTRA_ARGS)
_BASE_EXTRA_ARGS = [
    '--benchmarks',
    'some_benchmark',
    '--pageset-repeat',
    '1',
    '--browser',
    'web-engine-shell',
] + _COMBINED_DEFAULT_EXTRA_ARGS
_TELEMETRY_COMMAND = [
    'luci-auth',
    'context',
    '--',
    'vpython',
    '../../testing/scripts/run_performance_tests.py',
    '../../content/test/gpu/run_telemetry_benchmark_fuchsia.py',
]
_BASE_SWARMING_TAGS = {}


class FromDictTest(unittest.TestCase):

  def testMinimumArgumentsWebEngine(self):
    quest = run_web_engine_telemetry_test.RunWebEngineTelemetryTest.FromDict(
        _BASE_ARGUMENTS)
    expected = run_web_engine_telemetry_test.RunWebEngineTelemetryTest(
        'server', run_test_test.DIMENSIONS, _BASE_EXTRA_ARGS,
        _BASE_SWARMING_TAGS, _TELEMETRY_COMMAND, 'out/Release')
    self.assertEqual(quest, expected)
