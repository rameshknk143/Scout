import unittest
from datetime import datetime,timedelta,timezone
from weekly_watchdog import assess


class WatchdogTests(unittest.TestCase):
    def test_healthy_stale_degraded_and_capacity(self):
        now=datetime.now(timezone.utc)
        self.assertEqual(assess((now,'OK',{}),1,now),[])
        self.assertTrue(assess(None,1,now))
        self.assertTrue(assess((now-timedelta(hours=7),'OK',{}),1,now))
        self.assertTrue(assess((now,'DEGRADED',{}),1,now))
        self.assertTrue(assess((now,'OK',{}),460*1024*1024,now))
