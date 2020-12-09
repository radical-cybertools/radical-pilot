
# pylint: disable=protected-access, unused-argument, no-value-for-parameter

import os
import pytest

from unittest import mock

import radical.utils as ru

from   .test_common                          import setUp
from   radical.pilot.agent.launch_method.ssh import SSH


# ------------------------------------------------------------------------------
#
@mock.patch.object(SSH, '__init__',   return_value=None)
@mock.patch('radical.utils.raise_on')
@mock.patch('radical.utils.which', return_value='/usr/bin/ssh')
def test_configure(mocked_init, mocked_raise_on, mocked_which):

    cmd_str = '/usr/bin/ssh -o StrictHostKeyChecking=no -o ControlMaster=auto'
    component = SSH(name=None, cfg=None, session=None)
    component._configure()
    assert(cmd_str == component.launch_command)


# ------------------------------------------------------------------------------
#
@mock.patch.object(SSH, '__init__',   return_value=None)
@mock.patch('radical.utils.raise_on')
@mock.patch('radical.utils.which', return_value=None)
def test_configure_fail(mocked_init, mocked_raise_on, mocked_which):

    component = SSH(name=None, cfg=None, session=None)
    with pytest.raises(RuntimeError):
        component._configure()


# ------------------------------------------------------------------------------
#
@mock.patch.object(SSH, '__init__',   return_value=None)
@mock.patch.object(SSH, '_configure', return_value=None)
@mock.patch.dict(os.environ,
                 {'PATH': 'test_path', 'LD_LIBRARY_PATH': '/usr/local/lib/'},
                 clear=True)
@mock.patch('radical.utils.raise_on')
def test_construct_command(mocked_init,
                           mocked_configure,
                           mocked_raise_on):

    test_cases = setUp('lm', 'ssh')
    component  = SSH(name=None, cfg=None, session=None)

    component._log           = ru.Logger('dummy')
    component.name           = 'SSH'
    component.mpi_flavor     = None
    component.launch_command = 'ssh'
    component.ccmrun_command = ''
    component.dplace_command = ''

    for unit, result in test_cases:
        if result == "ValueError":
            with pytest.raises(ValueError):
                command, hop = component.construct_command(unit, None)
        elif result == "RuntimeError":
            with pytest.raises(RuntimeError):
                command, hop = component.construct_command(unit, 1)
        else:
            command, hop = component.construct_command(unit, 1)
            assert([command, hop] == result)


# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
