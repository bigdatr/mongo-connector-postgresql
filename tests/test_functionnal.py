# -*- coding: utf-8 -*-

from unittest import TestCase, main

import subprocess
import signal


class TestFunctionnal(TestCase):
    def setUp(self):
        self.DEVNULL = open('/dev/null', 'w')
        self.mongo_orchestration = subprocess.Popen(
            "mongo-orchestration start --no-fork".split(' '),
            stdout=self.DEVNULL,
            stderr=self.DEVNULL
        )

    def test_features(self):
        retcode = subprocess.call('aloe', shell=True)
        self.assertEqual(retcode, 0)

    def tearDown(self):
        self.mongo_orchestration.send_signal(signal.SIGTERM)
        self.mongo_orchestration.wait()
        self.DEVNULL.close()


if __name__ == '__main__':
    main()
