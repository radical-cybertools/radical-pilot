
__copyright__ = 'Copyright 2013-2020, http://radical.rutgers.edu'
__license__   = 'MIT'


import os
import time
import queue
import errno

import threading     as mt
import radical.utils as ru

from ...  import states    as rps
from ...  import constants as rpc

from .base import AgentExecutingComponent


# ------------------------------------------------------------------------------
#
class Flux(AgentExecutingComponent) :

    # --------------------------------------------------------------------------
    #
    def __init__(self, cfg, session):

        AgentExecutingComponent.__init__(self, cfg, session)


    # --------------------------------------------------------------------------
    #
    def initialize(self):
        '''
        This components has 3 strands of activity (threads):

          - the main thread listens for incoming tasks from the scheduler, and
            pushes them toward the watcher thread;
          - an event listener thread listens for flux events which signify task
            state updates, and pushes those events also to the watcher thread;
          - the watcher thread matches events and tasks, enacts state updates,
            and pushes completed tasks toward output staging.

        NOTE: we get tasks in *AGENT_SCHEDULING* state, and enact all
              further state changes in this component.
        '''

        # translate Flux states to RP states
        self._event_map = {'NEW'     : None,   # rps.AGENT_SCHEDULING,
                           'DEPEND'  : None,
                           'SCHED'   : rps.AGENT_EXECUTING_PENDING,
                           'RUN'     : rps.AGENT_EXECUTING,
                           'CLEANUP' : None,
                           'INACTIVE': rps.AGENT_STAGING_OUTPUT_PENDING,
                          }

        # thread termination signal
        self._term    = mt.Event()

        # need two queues, for tasks and events
        self._task_q  = queue.Queue()
        self._event_q = queue.Queue()

        # run listener thread
        self._listener_setup  = mt.Event()
        self._listener        = mt.Thread(target=self._listen)
        self._listener.daemon = True
        self._listener.start()

        # run watcher thread
        self._watcher_setup  = mt.Event()
        self._watcher        = mt.Thread(target=self._watch)
        self._watcher.daemon = True
        self._watcher.start()

        # main thread waits for tasks to arrive from the scheduler
        self.register_input(rps.AGENT_SCHEDULING,
                            rpc.AGENT_EXECUTING_QUEUE, self.work)

        # also listen on the command channel for task cancellation requests
        self.register_subscriber(rpc.CONTROL_PUBSUB, self.command_cb)

        # wait for some time to get watcher and listener initialized
        start = time.time()
        while time.time() - start < 10.0:
            if self._watcher_setup.is_set() and \
               self._listener_setup.is_set():
                break

        assert(self._watcher_setup.is_set())
        assert(self._listener_setup.is_set())


    # --------------------------------------------------------------------------
    #
    def command_cb(self, topic, msg):

        self._log.info('command_cb [%s]: %s', topic, msg)

        cmd = msg['cmd']
      # arg = msg['arg']

        if cmd == 'cancel_units':

            # FIXME: clarify how to cancel tasks in Flux
            pass

        return True


    # --------------------------------------------------------------------------
    #
    def work(self, units):

        self._task_q.put(ru.as_list(units))

        if self._term.is_set():
            self._log.warn('threads triggered termination')
            self.stop()


    # --------------------------------------------------------------------------
    #
    def _get_flux_handle(self):

        import flux
        
        flux_uri = self._cfg['rm_info']['lm_info']['flux_env']['FLUX_URI']
        return flux.Flux(url=flux_uri)


    # --------------------------------------------------------------------------
    #
    def _listen(self):

        flux_handle = None

        try:
            # thread local initialization
            flux_handle = self._get_flux_handle()

            flux_handle.event_subscribe('job-state')

            # FIXME: how tot subscribe for task return code information?
            def _flux_cb(self, *args, **kwargs):
                self._log.debug('==== flux cb    %s' % [args, kwargs])
           
            # signal successful setup to main thread
            self._listener_setup.set()

            while not self._term.is_set():

                # `recv()` will raise an `OSError(errno=EIO)` exception once the
                # flux instance terminated.  That is to be expected during
                # termination, and we'll bail out peacefully in that case.
                try:
                    event = flux_handle.event_recv()
                except OSError as e:
                    if e.errno == errno.EIO and self._term.is_set():
                        self._log.debug('lost flux during termination')
                        break
                    else:
                        raise RuntimeError('list flux connection') from e

                self._log.debug('==== flux event %s' % [event.payload])

                if 'transitions' not in event.payload:
                    self._log.warn('unexpected flux event: %s' %
                                    event.payload)
                    continue

                transitions = ru.as_list(event.payload['transitions'])

                self._event_q.put(transitions)


        except Exception:

            self._log.exception('=== Error in listener loop')

            if flux_handle:
                flux_handle.event_unsubscribe('job-state')

            self._term.set()


    # --------------------------------------------------------------------------
    #
    def handle_events(self, flux_handle, task, events):
        '''
        Return `True` on final events so that caller can clean caches.
        Note that this relies on Flux events to arrive in order
        (or at least in ordered bulks).
        '''

        import flux.job as fjob

        ret = False
        uid = task['uid']

        for event in events:

            flux_id    = event[0]
            flux_state = event[1]

            state = self._event_map[flux_state]

            if state is None:
                # ignore this state transition
                self._log.debug('ignore flux event %s:%s' %
                                (task['uid'], flux_state))
                continue

            self._log.debug('handle flux event %s:%s:%s' %
                            (task['uid'], flux_state, state))

            # FIXME: how to get actual event transition timestamp?
          # ts = event.time
            ts = time.time()

            if state == rps.AGENT_STAGING_OUTPUT_PENDING:

                task['target_state'] = rps.DONE  # FIXME
                ret = True

                # sift through the job's event log to see what happened to it
                # return
                for event in fjob.event_watch(flux_handle, flux_id, 'eventlog'):

                    self._log.debug('==== el: %s', event)

                    if event.name == 'alloc':
                        # FIXME: check if `alloc` is not `schedule_start`, and
                        #        `schedule_ok` maps to `debug.start-request`
                        self._prof.prof('schedule_ok', uid=uid, ts=event.timestamp, 
                                state=rps.AGENT_EXECUTING_PENDING, msg=event.context)
                        self.advance(task, rps.AGENT_EXECUTING_PENDING, ts=ts,
                                           publish=True, push=False)

                    elif event.name == 'start':
                        self.advance(task, rps.AGENT_EXECUTING, ts=ts,
                                           publish=True, push=False)

                    elif event.name == 'finish':
                        retval = event.context.get('status')
                        self._prof.prof('advance', uid=uid, ts=event.timestamp, 
                                state=rps.AGENT_STAGING_OUTPUT_PENDING, 
                                msg=event.context)

                    elif event.name == 'debug.free-request':
                        self._prof.prof('unschedule', state=rps.AGENT_EXECUTING, 
                             uid=uid, ts=event.timestamp, msg=event.context)

                    elif event.name == 'free':
                        self._prof.prof('unschedule_ok', uid=uid, 
                                ts=event.timestamp, msg=event.context,
                                state=rps.AGENT_EXECUTING)

                # on completion, push toward output staging
                self.advance(task, state, ts=ts, publish=True, push=True)

            else:
                # otherwise only push a state update
                self.advance(task, state, ts=ts, publish=True, push=False)

        return ret


    # --------------------------------------------------------------------------
    #
    def _watch(self):

        flux_handle = self._get_flux_handle()

        try:

            # thread local initialization
            tasks  = dict()
            events = dict()

            self.register_output(rps.AGENT_STAGING_OUTPUT_PENDING,
                                 rpc.AGENT_STAGING_OUTPUT_QUEUE)

            # signal successful setup to main thread
            self._watcher_setup.set()

            while not self._term.is_set():

                active = False

                try:
                    for task in self._task_q.get_nowait():

                        flux_id = task['flux_id']
                        assert flux_id not in tasks
                        tasks[flux_id] = task

                        # handle and purge cached events for that task
                        if flux_id in events:
                            if self.handle_events(flux_handle, task,
                                                  events[flux_id]):
                                # task completed - purge data
                                # NOTE: this assumes events are ordered
                                if flux_id in events: del(events[flux_id])
                                if flux_id in tasks : del(tasks[flux_id])

                    active = True

                except queue.Empty:
                    # nothing found -- no problem, check if we got some events
                    pass


                try:

                    for event in self._event_q.get_nowait():

                        self._log.debug('=== ev : %s', event)
                        self._log.debug('=== ids: %s', tasks.keys())

                        flux_id = event[0]
                        if flux_id in tasks:

                            # known task - handle events
                            if self.handle_events(flux_handle, tasks[flux_id],
                                                               [event]):
                                # task completed - purge data
                                # NOTE: this assumes events are ordered
                                if flux_id in events: del(events[flux_id])
                                if flux_id in tasks : del(tasks[flux_id])

                        else:
                            # unknown task, store events for later
                            if flux_id not in events:
                                events[flux_id] = list()
                            events[flux_id].append(event)

                    active = True

                except queue.Empty:
                    # nothing found -- no problem, check if we got some tasks
                    pass

                if not active:
                    time.sleep(0.01)


        except Exception:
            self._log.exception('=== Error in watcher loop')
            self._term.set()


# ------------------------------------------------------------------------------

