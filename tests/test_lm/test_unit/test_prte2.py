
# pylint: disable=protected-access, unused-argument, no-value-for-parameter

import pytest

from unittest import mock

import radical.utils as ru

from .test_common                            import setUp
from radical.pilot.agent.launch_method.prte2 import PRTE2


# ------------------------------------------------------------------------------
#
@mock.patch.object(PRTE2, '__init__', return_value=None)
@mock.patch.object(PRTE2, '_configure', return_value='prun')
def test_construct_command(mocked_init, mocked_configure):

    test_cases = setUp('lm', 'prte2')

    component = PRTE2(name=None, cfg=None, session=None)

    component.name           = 'prte2'
    component._verbose       = None
    component._log           = ru.Logger('dummy')
    component.launch_command = 'prun'

    for unit, result in test_cases:

        if result == 'RuntimeError':
            with pytest.raises(RuntimeError):
                command, hop = component.construct_command(unit, None)

        else:
            command, hop = component.construct_command(unit, None)
            assert([command, hop] == result), unit['uid']


# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
