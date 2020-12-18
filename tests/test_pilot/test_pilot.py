#!/usr/bin/env python3

import time

from   unittest import mock
from   unittest import TestCase

import radical.pilot as rp


# ------------------------------------------------------------------------------
#
class TestPilot(TestCase):

    @mock.patch.object(rp.PilotManager, '__init__', return_value=None)
    def test_pilot_uid(self, mocked_pmgr):

        pmgr = rp.PilotManager(session=None)
        pmgr._uids    = list()
        pmgr._uid     = 'pmgr.0000'
        pmgr._log     = mock.Mock()
        pmgr._prof    = mock.Mock()
        pmgr._session = mock.Mock()
        pmgr._session.uid = str(time.time())  # restart uid counter

        descr = rp.ComputePilotDescription({'resource': 'foo', 'uid': 'foo'})
        self.assertEqual(rp.ComputePilot(pmgr, descr).uid, 'foo')

        with self.assertRaises(ValueError):
            rp.ComputePilot(pmgr, descr)

        descr = rp.ComputePilotDescription({'resource': 'foo'})
        self.assertEqual(rp.ComputePilot(pmgr, descr).uid, 'pilot.0000')

        descr = rp.ComputePilotDescription({'resource': 'foo', 'uid': 'bar'})
        self.assertEqual(rp.ComputePilot(pmgr, descr).uid, 'bar')

        with self.assertRaises(ValueError):
            rp.ComputePilot(pmgr, descr)

        descr = rp.ComputePilotDescription({'resource': 'foo'})
        self.assertEqual(rp.ComputePilot(pmgr, descr).uid, 'pilot.0001')


# ------------------------------------------------------------------------------
#
if __name__ == '__main__':

    tc = TestPilot()
    tc.test_pilot_uid()


# ------------------------------------------------------------------------------

