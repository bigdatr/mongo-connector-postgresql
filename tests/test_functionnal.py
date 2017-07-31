# -*- coding: utf-8 -*-

from unittest import TestCase, main

import subprocess
import signal


class TestFunctionnal(TestCase):
    def setUp(self):
        self.mongo_orchestration = subprocess.Popen(
            "mongo-orchestration start --no-fork".split(' ')
        )

    def test_features(self):
        retcode = subprocess.call('aloe', shell=True)

    def tearDown(self):
        self.mongo_orchestration.send_signal(signal.SIGTERM)
        self.mongo_orchestration.wait()


if __name__ == '__main__':
    main()
