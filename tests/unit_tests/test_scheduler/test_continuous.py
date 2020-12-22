
# pylint: disable=protected-access, no-value-for-parameter, unused-argument

__copyright__ = "Copyright 2013-2016, http://radical.rutgers.edu"
__license__ = "MIT"

import glob
import pytest
import os

from unittest import TestCase
from unittest import mock

import radical.utils           as ru
import radical.pilot.constants as rpc

from   radical.pilot.agent.scheduler.continuous import Continuous


# ------------------------------------------------------------------------------
#
class TestContinuous(TestCase):

    # --------------------------------------------------------------------------
    #
    def setUp(self):

        ret = list()
        pat = os.path.dirname(__file__) + '/test_cases_continuous/unit*.json'

        for fin in glob.glob(pat):
            test_cases = ru.read_json(fin)
            ret.append(test_cases)

        cfg_fname = os.path.dirname(__file__) + '/test_cases_continuous/test_continuous.json'
        cfg_tests = ru.read_json(cfg_fname)

        return cfg_tests, ret


    # --------------------------------------------------------------------------
    #
    def tearDown(self):
        pass


    # --------------------------------------------------------------------------
    #
    @mock.patch.object(Continuous, '__init__', return_value=None)
    def test_configure(self, mocked_init):

        component = Continuous(cfg=None, session=None)
        component._uid = 'agent_scheduling.0000'
        component._log = ru.Logger('dummy')

        # 1) without blocked cores; 2) with blocked cores;
        blocked_cores_list = [[], [0, 1]]

        test_case, _ = self.setUp()
        for rm_info in test_case['configure']['rm_info']:

            component._rm_info           = rm_info
            component._rm_lm_info        = rm_info['lm_info']
            component._rm_node_list      = rm_info['node_list']
            component._rm_cores_per_node = rm_info['cores_per_node']
            component._rm_gpus_per_node  = rm_info['gpus_per_node']
            component._rm_lfs_per_node   = rm_info['lfs_per_node']
            component._rm_mem_per_node   = rm_info['mem_per_node']

            for blocked_cores in blocked_cores_list:

                if blocked_cores:
                    # add the index of the last core to the blocked cores
                    blocked_cores  = blocked_cores[:]
                    blocked_cores += [rm_info['cores_per_node'] - 1]

                component._cfg = ru.Config(from_dict={
                    'pid'         : 'pilot.0000',
                    'rm_info'     : rm_info,
                    'resource_cfg': {
                        'blocked_cores': blocked_cores
                    }
                })

                component._configure()

                try:

                    self.assertEqual(
                        component.nodes[0]['cores'],
                        [rpc.FREE] * rm_info['cores_per_node'])
                    self.assertEqual(
                        component.nodes[0]['gpus'],
                        [rpc.FREE] * rm_info['gpus_per_node'])

                except AssertionError:

                    blocked_core_idx = blocked_cores[-1]
                    self.assertEqual(
                        component.nodes[0]['cores'][blocked_core_idx],
                        rpc.DOWN)

                    self.assertEqual(
                        component._rm_cores_per_node,
                        rm_info['cores_per_node'] - len(blocked_cores))


    # --------------------------------------------------------------------------
    #
    @mock.patch.object(Continuous, '__init__', return_value=None)
    @mock.patch.object(Continuous, '_configure', return_value=None)
    def test_find_resources(self,
                            mocked_init,
                            mocked_configure):

        _, cfg = self.setUp()
        component = Continuous(cfg=None, session=None)
        component.node = {'name'  : 'a',
                          'uid'   : 2,
                          'cores' : [0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0],
                          'lfs'   : {"size": 1234,
                                     "path" : "/dev/null"},
                          'mem'   : 1024,
                          'gpus'  : [0, 0]}
        component._log = ru.Logger('dummy')
        component._rm_lfs_per_node = {"path" : "/dev/null", "size" : 1234}
        component.cores_per_slot   = 16
        component.gpus_per_slot    = 2
        component.lfs_per_slot     = 1234
        component.mem_per_slot     = 1024
        component.find_slot        = 1

        try:
            test_slot = component._find_resources(
                node=component.node,
                find_slots=component.find_slot,
                cores_per_slot=component.cores_per_slot,
                gpus_per_slot=component.gpus_per_slot,
                lfs_per_slot=component.lfs_per_slot,
                mem_per_slot=component.mem_per_slot,
                partial='None')
            self.assertEqual([cfg[1]['setup']['lm']['slots']], test_slot)
        except:
            with pytest.raises(AssertionError):
                raise


    # --------------------------------------------------------------------------
    #
    @mock.patch.object(Continuous, '__init__', return_value=None)
    @mock.patch.object(Continuous, '_configure', return_value=None)
    @mock.patch.object(Continuous, '_find_resources',
                       return_value=[{'name'    : 'a',
                                      'uid'     : 1,
                                      'core_map': [[0]],
                                      'gpu_map' : [[0]],
                                      'lfs'     : {'path': '/dev/null',
                                                   'size': 1234},
                                      'mem'     : 128}])
    def test_schedule_unit(self,
                           mocked_init,
                           mocked_configure,
                           mocked_find_resources):

        _, cfg = self.setUp()
        component = Continuous(cfg=None, session=None)
        unit = dict()
        unit['uid'] = cfg[1]['unit']['uid']
        unit['description'] = cfg[1]['unit']['description']
        component.nodes = cfg[1]['setup']['lm']['slots']['nodes']

        component._rm_cores_per_node = 32
        component._rm_gpus_per_node  = 2
        component._rm_lfs_per_node   = {"size": 0, "path": "/dev/null"}
        component._rm_mem_per_node   = 1024
        component._rm_lm_info = 'INFO'
        component._log = ru.Logger('dummy')
        component._node_offset = 0
        test_slot =  {'cores_per_node': 32,
                      'gpus_per_node': 2,
                      'lfs_per_node': {'path': '/dev/null', 'size': 0},
                      'lm_info': 'INFO',
                      'mem_per_node': 1024,
                      'nodes': [{'core_map': [[0]],
                                 'gpu_map' : [[0]],
                                 'lfs': {'path': '/dev/null', 'size': 1234},
                                 'mem': 128,
                                 'name': 'a',
                                 'uid': 1}]}
        try:
            self.assertEqual(component.schedule_unit(unit), test_slot)
        except:
            with pytest.raises(AssertionError):
                raise


    # --------------------------------------------------------------------------
    #
    @mock.patch.object(Continuous, '__init__', return_value=None)
    def test_unschedule_unit(self, mocked_init):

        component = Continuous(cfg=None, session=None)
        _, cfg   = self.setUp()

        unit = {
                'description': cfg[1]['unit']['description'],
                'slots'      : cfg[1]['setup']['lm']['slots']
               }

        component.nodes = cfg[1]['setup']['lm']['slots']['nodes']
        component._log  = ru.Logger('dummy')

        component.unschedule_unit(unit)
        try:
            self.assertEqual(component.nodes[0]['cores'], [0])
            self.assertEqual(component.nodes[0]['gpus'], [0])
        except:
            with pytest.raises(AssertionError):
                raise


# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
