
import os
import sys

import radical.pilot as rp

# ARCHER:
# =======
# 
# Create a virtualenv
#
#   wget --no-check-certificate https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.tar.gz
#   tar xzf virtualenv-1.10.tar.gz
#   python virtualenv-1.10/virtualenv.py $HOME/RP
#   source $HOME/RP/bin/activate
#
# Download and install RADICAL-Pilot: 
#
#   git clone https://github.com/radical-cybertools/radical.pilot.git
#   cd radical.pilot
#   git checkout devel
#   easy_install .
# 
# Run this script with the remote MongoDB server.
#
#   cd tests
#  
# Change: 
#     "pdesc.sandbox" to appropriate path
#     "pdesc.project" to your project allocation
#     
# Next, run the example
#
#   export RADICAL_PILOT_DBURL=mongodb://ec2-184-72-89-141.compute-1.amazonaws.com:27017/
#   RADICAL_PILOT_VERBOSE=info python archer_test.py
#

# DBURL defines the MongoDB server URL and has the format mongodb://host:port.
# For the installation of a MongoDB server, refer to http://docs.mongodb.org.
DBURL = os.getenv("RADICAL_PILOT_DBURL")
if DBURL is None:
    print "ERROR: RADICAL_PILOT_DBURL (MongoDB server URL) is not defined."
    sys.exit(1)


#------------------------------------------------------------------------------
#
def pilot_state_cb(pilot, state):
    """pilot_state_change_cb() is a callback function. It gets called very
    time a ComputePilot changes its state.
    """
    print "[AppCallback]: ComputePilot '{0}' state changed to {1}.".format(
        pilot.uid, state)

    if state == rp.states.FAILED:
        sys.exit(1)


#------------------------------------------------------------------------------
#
def unit_state_change_cb(unit, state):
    """unit_state_change_cb() is a callback function. It gets called very
    time a ComputeUnit changes its state.
    """
    print "[AppCallback]: ComputeUnit '{0}' state changed to {1}.".format(
        unit.uid, state)
    if state == rp.states.FAILED:
        print "            Log: %s" % unit.log[-1]


#------------------------------------------------------------------------------
#
if __name__ == "__main__":

    try:
        # Create a new session. A session is the 'root' object for all other
        # RADICAL-Pilot objects. It encapsualtes the MongoDB connection(s) as
        # well as security crendetials.
        session = rp.Session(database_url=DBURL)

        # Add a Pilot Manager. Pilot managers manage one or more ComputePilots.
        pmgr = rp.PilotManager(session=session)

        # Register our callback with the PilotManager. This callback will get
        # called every time any of the pilots managed by the PilotManager
        # change their state.
        pmgr.register_callback(pilot_state_cb)

        pdesc = rp.ComputePilotDescription()
        pdesc.resource         = "archer.ac.uk"
        pdesc.project          = "e290"  # archer 'project group'
        pdesc.runtime          = 10
        pdesc.cores            = 56      # there are 24 cores per node on Archer, so this allocates 3 nodes
        pdesc.sandbox          = "/work/e290/e290/merzky/radical.pilot.sandbox/" 
        pdesc.cleanup          = False


        # Launch the pilot.
        pilot = pmgr.submit_pilots(pdesc)

        compute_units = []

        for unit_count in range(0, 8):

            mpi_test_task = rp.ComputeUnitDescription()
            mpi_test_task.executable  = "/bin/hostname"
            mpi_test_task.cores       = 4
            compute_units.append(mpi_test_task)

        # Combine the ComputePilot, the ComputeUnits and a scheduler via
        # a UnitManager object.
        umgr = rp.UnitManager(
            session=session,
            scheduler=rp.SCHED_DIRECT_SUBMISSION)

        # Register our callback with the UnitManager. This callback will get
        # called every time any of the units managed by the UnitManager
        # change their state.
        umgr.register_callback(unit_state_change_cb)

        # Add the previsouly created ComputePilot to the UnitManager.
        umgr.add_pilots(pilot)

        # Submit the previously created ComputeUnit descriptions to the
        # PilotManager. This will trigger the selected scheduler to start
        # assigning ComputeUnits to the ComputePilots.
        units = umgr.submit_units(compute_units)

        # Wait for all compute units to reach a terminal state (DONE or FAILED).
        umgr.wait_units()

        for unit in units:
            print "* Task %s - state: %s, exit code: %s, started: %s, finished: %s" \
                % (unit.uid, unit.state, unit.exit_code, unit.start_time, unit.stop_time)

        session.close()
        sys.exit(0)

    except rp.PilotException, ex:
        # Catch all exceptions and exit with and error.
        print "Error during execution: %s" % ex
        sys.exit(1)

