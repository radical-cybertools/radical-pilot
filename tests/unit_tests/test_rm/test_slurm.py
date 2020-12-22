# pylint: disable=protected-access, unused-argument, no-value-for-parameter

import os
import pytest

from unittest import mock

import radical.utils as ru

from radical.pilot.agent.resource_manager.slurm import Slurm


# ------------------------------------------------------------------------------
#
@mock.patch.object(Slurm, '__init__',   return_value=None)
@mock.patch('radical.utils.raise_on')
@mock.patch('hostlist.expand_hostlist', return_value=['nodes1', 'nodes2'])
def test_configure(mocked_init, mocked_raise_on, mocked_expand_hostlist):

    # Test 1 no config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    os.environ['SLURM_NPROCS'] = '48'
    os.environ['SLURM_NNODES'] = '2'
    os.environ['SLURM_CPUS_ON_NODE'] = '24'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {}
    component.lm_info = {'cores_per_node': None}
    component._configure()

    assert component.node_list == [['nodes1','nodes1'],['nodes2','nodes2']]
    assert component.cores_per_node == 24
    assert component.gpus_per_node == 0
    assert component.lfs_per_node == {'path': None, 'size': 0}

    # Test 2 config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    os.environ['SLURM_NPROCS'] = '48'
    os.environ['SLURM_NNODES'] = '2'
    os.environ['SLURM_CPUS_ON_NODE'] = '24'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {'cores_per_node': 24,
                      'gpus_per_node': 1,
                      'lfs_path_per_node': 'test/',
                      'lfs_size_per_node': 100}
    component.lm_info = {'cores_per_node': None}
    component._configure()
    assert component.node_list == [['nodes1','nodes1'],['nodes2','nodes2']]
    assert component.cores_per_node == 24
    assert component.gpus_per_node == 1
    assert component.lfs_per_node == {'path': 'test/', 'size': 100}

    # Test 3 config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    os.environ['SLURM_NPROCS'] = '48'
    os.environ['SLURM_NNODES'] = '2'
    os.environ['SLURM_CPUS_ON_NODE'] = '24'
    os.environ['LOCAL'] = '/local_folder/'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {'cores_per_node': 24,
                      'gpus_per_node': 1,
                      'lfs_path_per_node': '${LOCAL}',
                      'lfs_size_per_node': 100}
    component.lm_info = {'cores_per_node': None}
    component._configure()
    assert component.node_list == [['nodes1','nodes1'],['nodes2','nodes2']]
    assert component.cores_per_node == 24
    assert component.gpus_per_node == 1
    assert component.lfs_per_node == {'path': '/local_folder/', 'size': 100}

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
#
@mock.patch.object(Slurm, '__init__',   return_value=None)
@mock.patch('radical.utils.raise_on')
@mock.patch('hostlist.expand_hostlist', return_value=['nodes1', 'nodes2'])
def test_configure_error(mocked_init, mocked_raise_on, mocked_expand_hostlist):

    # Test 1 no config file
    if 'SLURM_NODELIST' in os.environ:
        del os.environ['SLURM_NODELIST']

    os.environ['SLURM_NPROCS'] = '48'
    os.environ['SLURM_NNODES'] = '2'
    os.environ['SLURM_CPUS_ON_NODE'] = '24'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {}
    component.lm_info = {}

    with pytest.raises(RuntimeError):
        component._configure()

    # Test 2 config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    del os.environ['SLURM_NPROCS']
    os.environ['SLURM_NNODES'] = '2'
    os.environ['SLURM_CPUS_ON_NODE'] = '24'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {}
    component.lm_info = {}

    with pytest.raises(RuntimeError):
        component._configure()

    # Test 2 config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    os.environ['SLURM_NPROCS'] = '48'
    del os.environ['SLURM_NNODES']
    os.environ['SLURM_CPUS_ON_NODE'] = '24'

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {}
    component.lm_info = {}

    with pytest.raises(RuntimeError):
        component._configure()

    # Test 2 config file
    os.environ['SLURM_NODELIST'] = 'nodes-[1-2]'
    os.environ['SLURM_NPROCS'] = '48'
    os.environ['SLURM_NNODES'] = '2'
    del os.environ['SLURM_CPUS_ON_NODE']

    component = Slurm(cfg=None, session=None)
    component._log = ru.Logger('dummy')
    component._cfg = {}
    component.lm_info = {}

    with pytest.raises(RuntimeError):
        component._configure()


# ------------------------------------------------------------------------------
# pylint: enable=protected-access, unused-argument, no-value-for-parameter
