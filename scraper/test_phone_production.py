import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import phone_production as worker


class ProductionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = patch.object(worker, 'BASE', Path(self.directory.name))
        self.base.start()
        self.addCleanup(self.base.stop)
        self.now = patch.object(worker.time, 'time', return_value=1000000)
        self.clock = self.now.start()
        self.addCleanup(self.now.stop)
        self.calls = []

    def capture(self, path, payload=None):
        self.calls.append(path)
        if path.startswith('/phone/catalog'):
            return {'batch': {'rows': [{'asin': 'B012345678'}],
                             'captured_at': '2026-10-24T00:00:00Z',
                             'next_token': 'second-page'}, 'proof': 'fixture-proof'}
        return {'ok': True, 'verified': 1, 'inserted': 1}

    def test_cursor_survives_ticks_and_same_slot_never_recaptures(self):
        with patch.object(worker, 'call', side_effect=self.capture):
            self.assertEqual(worker.tick(), 'captured')
            self.assertEqual(worker.tick(), 'already_recorded')
            self.clock.return_value += 90
            self.assertEqual(worker.tick(), 'captured')
        self.assertIn('page_token=second-page', self.calls[-1])
        self.assertEqual(len(self.calls), 3)

    def test_failed_delivery_retains_exact_capture_and_prevents_new_capture(self):
        with patch.object(worker, 'call', side_effect=self.capture):
            worker.tick()
        with patch.object(worker, 'call', side_effect=HTTPError('https://invalid',503,'down',{},None)):
            self.clock.return_value += 90
            self.assertEqual(worker.tick(), 'delivery_pending')
        with sqlite3.connect(worker.BASE/'production-outbox.sqlite') as db:
            count, raw, delivered = db.execute('select rows,payload,delivered_at from captures').fetchone()
        db.close()
        self.assertEqual(count, 1)
        self.assertEqual(json.loads(raw)['proof'], 'fixture-proof')
        self.assertIsNone(delivered)

    def test_authorization_refusal_blocks_further_capture_calls(self):
        with patch.object(worker, 'call', side_effect=HTTPError('https://invalid',403,'denied',{},None)) as call:
            self.assertEqual(worker.tick(), 'failed')
            self.clock.return_value += 90
            self.assertEqual(worker.tick(), 'authorization_blocked')
            self.assertEqual(call.call_count, 1)

    def test_retry_after_is_obeyed_without_another_request(self):
        with patch.object(worker, 'call', side_effect=HTTPError('https://invalid',429,'slow',{'Retry-After':'600'},None)) as call:
            self.assertEqual(worker.tick(), 'failed')
            self.clock.return_value += 90
            self.assertEqual(worker.tick(), 'throttled_or_storage_pause')
            self.assertEqual(call.call_count, 1)


if __name__ == '__main__':
    unittest.main()

