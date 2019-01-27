
__copyright__ = "Copyright 2016, http://radical.rutgers.edu"
__license__   = "MIT"


import radical.utils as ru

from .base import LaunchMethod


# ==============================================================================
#
class JSRUN(LaunchMethod):

    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg, session):

        LaunchMethod.__init__(self, cfg, session)


    # --------------------------------------------------------------------------
    #
    def _configure(self):

        self.launch_command = ru.which('jsrun')

    # --------------------------------------------------------------------------
    #
    def _create_resource_set_file(self, slots, uid, sandbox):
        """
        This method takes as input a CU slots and creates the necessary
        resource set file. This resource set file is then use by jsrun to 
        place and execute tasks on nodes.

        An example of a resource file is:

        * Task 1: 2 MPI procs, 2 threads per process and 2 gpus per process*

            RS 0 : {host: 1 cpu:  0  1 gpu: 0 1}
            RS 1 : {host: 1 cpu: 22 23 gpu: 3 4}

        * Task 2: 2 MPI procs, 1 thread per process and 1 gpus per process*

            RS 0 : {host: 2 cpu:  7 gpu: 2}
            RS 1 : {host: 2 cpu: 30 gpu: 5}

        Parameters
        ----------
        slots : List of dictionaries.

            The slots that the unit will be placed. A slot has the following
            format:

            {"nodes"         : [{"name"    : "a",
                                 "uid"     : 1,
                                 "gpu_map" : [],
                                 "core_map": [[0]],
                                 "lfs"     : {"path": "/dev/null", "size": 0}
                                }],
             "cores_per_node": 16,
             "gpus_per_node" : 6
             "lfs_per_node"  : {"size": 0, "path": "/dev/null"},
             "lm_info"       : "INFO",
            }

        uid     : unit ID (string)
        sandbox : unit sandbox (string)

        """

        rs_id  = 0
        rs_str = ''

        import pprint
        self._log.debug('slots: \n%s', pprint.pprint(slots))

        for node in slots['nodes']:

            cores = ' '.join([str(core_set[0]) for core_set
                                               in  node['core_map']])
            gpus  = ' '.join([str(gpu_set[0])  for gpu_set
                                               in  node['gpu_map']])

            rs_str           += 'RS %d: {'  % rs_id
            rs_str           += ' host: %d' % node['uid']
            if cores: rs_str += ' cpu: %s'  % cores
            if gpus : rs_str += ' gpu: %s'  % gpus
            rs_str           += ' }\n'
            rs_id            += 1

        rs_name = '%s/%s.rs' % (sandbox, uid)
        with open(rs_name, 'w') as fout:
            fout.write(rs_str)      

        return rs_name


    # --------------------------------------------------------------------------
    #
    def construct_command(self, cu, launch_script_hop):

        # FIXME: derive task_procs from slots (to include GPU)

        uid            = cu['uid']
        slots          = cu['slots']
        cud            = cu['description']
        task_exec      = cud['executable']
        task_procs     = cud.get('cpu_processes', 0)
        task_env       = cud.get('environment') or dict()
        task_args      = cud.get('arguments')   or list()
        task_argstr    = self._create_arg_string(task_args)
        task_sandbox   = ru.Url(cu['unit_sandbox']).path

        assert(slots), 'missing slots for %s' % uid

        self._log.debug('prep %s', uid)

        if task_argstr: task_command = "%s %s" % (task_exec, task_argstr)
        else          : task_command = task_exec

        env_list   = self.EXPORT_ENV_VARIABLES + task_env.keys()
        env_string = ' '.join(['-E "%s"' % var for var in env_list])

        rs_fname = self._create_resource_set_file(slots=slots, uid=uid,
                                                  sandbox=task_sandbox)

      # flags = '-n%d -a1 ' % (task_procs)
        command = '%s -U %s -a %d  %s %s' % (self.launch_command, rs_fname, 
                                             task_procs, env_string,
                                             task_command)
        return command, None


# ------------------------------------------------------------------------------

