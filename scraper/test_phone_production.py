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

    def test_five_page_cycle_delivers_each_page_and_preserves_gap(self):
        with patch.object(worker, 'call', side_effect=self.capture), patch.object(worker.time, 'sleep') as sleep, patch.object(worker.time, 'monotonic', return_value=0):
            self.assertEqual(worker.cycle(), 'cycle_complete')
            self.assertEqual(sum(x.startswith('/phone/catalog') for x in self.calls), 5)
            self.assertEqual(self.calls.count('/phone/deliver'), 5)
            self.assertEqual(sleep.call_args_list, [unittest.mock.call(12)]*4)
            before=len(self.calls)
            self.assertEqual(worker.cycle(), 'batch_gap')
            self.assertEqual(len(self.calls), before)
        db=sqlite3.connect(worker.BASE/'production-outbox.sqlite')
        try:
            self.assertEqual(db.execute('select count(*),count(delivered_at) from captures').fetchone(), (5,5))
        finally:
            db.close()

    def test_mid_cycle_throttle_stops_remaining_requests_and_retains_pages(self):
        def request(path,payload=None):
            if path.startswith('/phone/catalog') and sum(x.startswith('/phone/catalog') for x in self.calls)==2:
                self.calls.append(path)
                raise HTTPError('https://invalid',429,'slow',{'Retry-After':'600'},None)
            return self.capture(path,payload)
        with patch.object(worker,'call',side_effect=request), patch.object(worker.time,'sleep'):
            self.assertEqual(worker.cycle(),'failed')
            self.assertEqual(sum(x.startswith('/phone/catalog') for x in self.calls),3)
            self.clock.return_value+=90
            self.assertEqual(worker.cycle(),'throttled_or_storage_pause')
        db=sqlite3.connect(worker.BASE/'production-outbox.sqlite')
        try:
            self.assertEqual(db.execute('select count(*),count(delivered_at) from captures').fetchone(),(2,2))
        finally:
            db.close()

    def test_http_date_retry_after_is_not_shortened(self):
        from email.utils import formatdate
        error=HTTPError('https://invalid',429,'slow',{'Retry-After':formatdate(1000000+172800,usegmt=True)},None)
        self.assertEqual(worker.retry_delay(error,90),172800)

    def test_full_cycle_stores_and_delivers_one_hundred_rows(self):
        def request(path,payload=None):
            response=self.capture(path,payload)
            if path.startswith('/phone/catalog'):
                response['batch']['rows']=[{'asin':f'B{i:09d}'} for i in range(20)]
            else:
                response.update(verified=20,inserted=20)
            return response
        with patch.object(worker,'call',side_effect=request), patch.object(worker.time,'sleep'):
            self.assertEqual(worker.cycle(),'cycle_complete')
        db=sqlite3.connect(worker.BASE/'production-outbox.sqlite')
        try:
            self.assertEqual(db.execute('select sum(rows),count(delivered_at) from captures').fetchone(),(100,5))
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()

