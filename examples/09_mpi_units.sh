#!/bin/sh

# This script tests the correct startup of mixed OpenMP / MPI units via RP.
#
#   - for OpenMP, we expect RP to set OMP_NUM_THREADS to `cud.cpu_threads`.
#   - for MPI, we expect either `$PMI_RANK` (for MPICH) or `$PMIX_RANK` (for
#     OpenMPI) to be set.
#
# We thus check these env settings, and each thread will print its repsective
# `process:thread` ID pair on stdout.  The consumer of this output
# (`examples/09_mpi_units.py`) will have to check if the correct set of ID pairs
# is found.

OMP_NUM=$OMP_NUM_THREADS
MPI_RANK="$PMI_RANK$PMIX_RANK"

seq()  (i=0; while test $i -lt $1; do echo $i; i=$((i+1)); done)
fail() (echo "$*"; exit 1)

test -z "$OMP_NUM"  && fail 'OMP_NUM_THREADS not set'
test -z "$MPI_RANK" && fail 'PMI_RANK / PMIX_RANK not set'

for idx in $(seq $OMP_NUM); do (echo -n "$MPI_RANK:$idx ")& done
for idx in $(seq $OMP_NUM); do wait                       ; done

