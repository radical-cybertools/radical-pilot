#!/usr/bin/env python

__copyright__ = 'Copyright 2013-2014, http://radical.rutgers.edu'
__license__   = 'MIT'

import os
import sys

if 'RADICAL_REPORT' in os.environ:
    del(os.environ['RADICAL_REPORT'])

import radical.pilot as rp
import radical.utils as ru

pwd = os.path.abspath(os.path.dirname(__file__))


# ------------------------------------------------------------------------------
#
def test_ordered_scheduler():

    report = ru.Reporter(name='radical.pilot')
    report.title('Getting Started (RP version %s)' % rp.version)

    session = rp.Session()

    try:
        # read the config used for resource details
        report.info('read config')
        report.ok('>>ok\n')

        report.header('submit pilots')

        pd_init = {'resource'      : 'local.localhost',
                   'runtime'       : 5,
                   'exit_on_error' : True,
                   'cores'         : 10
                  }
        pdesc = rp.ComputePilotDescription(pd_init)
        pmgr  = rp.PilotManager(session=session)
        pilot = pmgr.submit_pilots(pdesc)

        report.header('submit pipelines')

        umgr = rp.UnitManager(session=session)
        umgr.add_pilots(pilot)

        n_pipes  = 2
        n_stages = 5
        n_tasks  = 4

        cuds = list()
        for p in range(n_pipes):
            for s in range(n_stages):
                for t in range(n_tasks):
                    cud = rp.ComputeUnitDescription()
                    cud.executable       = '%s/pipeline_task.sh' % pwd
                    cud.arguments        = [p, s, t, 10]
                    cud.cpu_processes    = 1
                    cud.tags             = {'order': {'ns'   : p,
                                                      'order': s,
                                                      'size' : n_tasks}}
                    cud.name             =  'p%03d-s%03d-t%03d' % (p, s, t)
                    cuds.append(cud)
                    report.progress()

        import random
        random.shuffle(cuds)

        # Submit the previously created ComputeUnit descriptions to the
        # PilotManager. This will trigger the selected scheduler to start
        # assigning ComputeUnits to the ComputePilots.
        umgr.submit_units(cuds)

        # Wait for all compute units to reach a final state
        report.header('gather results')
        umgr.wait_units()


    except Exception as e:
        # Something unexpected happened in the pilot code above
        report.error('caught Exception: %s\n' % e)
        ru.print_exception_trace()
        raise

    except (KeyboardInterrupt, SystemExit) as e:
        # the callback called sys.exit(), and we can here catch the
        # corresponding KeyboardInterrupt exception for shutdown.  We also catch
        # SystemExit (which gets raised if the main threads exits for some other
        # reason).
        ru.print_exception_trace()
        report.warn('exit requested\n')

    finally:
        # always clean up the session, no matter if we caught an exception or
        # not.  This will kill all remaining pilots.
        report.header('finalize')
        session.close(download=False)

    report.header()


# ------------------------------------------------------------------------------

