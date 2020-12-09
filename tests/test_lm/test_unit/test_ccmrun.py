
# pylint: disable=protected-access, unused-argument, no-value-for-parameter

from unittest import mock

from   .test_common                             import setUp
from   radical.pilot.agent.launch_method.ccmrun import CCMRun

import radical.utils as ru


# ------------------------------------------------------------------------------
#
@mock.patch.object(CCMRun, '__init__',   return_value=None)
@mock.patch('radical.utils.raise_on')
@mock.patch('radical.utils.which', return_value='/usr/bin/ccmrun')
def test_configure(mocked_init, mocked_raise_on, mocked_which):

    component = CCMRun(name=None, cfg=None, session=None)
    component._configure()
    assert('/usr/bin/ccmrun' == component.launch_command)


# ------------------------------------------------------------------------------
#
@mock.patch.object(CCMRun, '__init__',   return_value=None)
@mock.patch.object(CCMRun, '_configure', return_value=None)
@mock.patch('radical.utils.raise_on')
def test_construct_command(mocked_init,
                           mocked_configure,
                           mocked_raise_on):

    test_cases = setUp('lm', 'ccmrun')
    component  = CCMRun(name=None, cfg=None, session=None)

    component._log           = ru.Logger('dummy')
    component.name           = 'CCMRun'
    component.mpi_flavor     = None
    component.launch_command = 'ccmrun'
    component.ccmrun_command = ''
    component.dplace_command = ''

    for unit, result in test_cases:
        command, hop = component.construct_command(unit, None)
        assert([command, hop] == result)


# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
