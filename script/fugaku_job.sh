#!/bin/sh
#PJM --rsc-list "node=192"
#PJM --rsc-list "elapse=4:00:00"
#PJM --rsc-list "rscgrp=small"
#PJM --mpi "max-proc-per-node=4"
#PJM -S

export OMP_NUM_THREADS=12

mpiexec -stdout-proc ./%/1000R/stdout -stderr-proc ./%/1000R/stderr ../cmake-build-release/main_ExhaustiveSearch --params '{"N":50,"mu_assess1":0.02,"mu_assess2":0.02,"mu_impl":0.02,"t_init":5000,"t_measure":5000}' --rd-start 0 --rd-end 255 --rr-start 0 --rr-end 255 --out all_norms.tsv
