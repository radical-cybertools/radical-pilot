
# pylint: disable=protected-access, unused-argument, no-value-for-parameter
#
__copyright__ = "Copyright 2013-2016, http://radical.rutgers.edu"

import unittest

from unittest import mock

import radical.utils as ru

from radical.pilot.agent.executing.shell import Shell


# ------------------------------------------------------------------------------
#
class TestBase(unittest.TestCase):

    # ------------------------------------------------------------------------------
    #
    def setUp(self):

        fname = 'tests/test_executing/test_unit/test_cases/test_base.json'

        return ru.read_json(fname)

    # --------------------------------------------------------------------------
    #
    @mock.patch.object(Shell, '__init__', return_value=None)
    @mock.patch.object(Shell, 'initialize', return_value=None)
    def test_handle_unit(self, mocked_init, mocked_initialize):

        global_launcher = []
        global_cu = []

        def spawn_side_effect(launcher, cu):
            nonlocal global_launcher
            nonlocal global_cu
            global_launcher.append(launcher)
            global_cu.append(cu)

        tests = self.setUp()
        cu = dict()
        cu['uid']         = tests['unit']['uid']
        cu['description'] = tests['unit']['description']
        cu['stderr']      = 'tests/test_executing/test_unit/test_cases/'

        component = Shell()
        component._cus_to_cancel         = []
        component._prof                  = mock.Mock()
        component.publish                = mock.Mock()
        component._mpi_launcher          = mock.Mock()
        component._mpi_launcher.name     = 'mpiexec'
        component._mpi_launcher.command  = 'mpiexec'
        component._task_launcher         = mock.Mock()
        component._task_launcher.name    = 'ssh'
        component._task_launcher.command = 'ssh'
        component._log                   = ru.Logger('dummy')

        component.spawn = mock.MagicMock(side_effect=spawn_side_effect
                (launcher=component._mpi_launcher, cu=cu))

        component._handle_unit(cu)
        self.assertEqual(cu, global_cu[0])

# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
