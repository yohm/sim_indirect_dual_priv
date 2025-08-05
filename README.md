# Prerequisites

- cmake
- OpenMP
- Eigen3
- nlohmann-json

Install these prerequisites by homebrew if you are on macOS.

```bash
brew install cmake
brew install libomp
brew install eigen
brew install nlohmann-json
```

# Build

Clone the repository with submodules.

```bash
git clone --recursive git@github.com:yohm/sim_indiredct_dual_priv.git
cd sim_indiredct_dual_priv
```

Make a build directory and run cmake.

```bash
mkdir cmake-build-debug
cd cmake-build-debug
cmake ..
cmake --build .
```

If you want to build in release mode, run cmake with `-DCMAKE_BUILD_TYPE=Release` option.

```bash
mkdir cmake-build-release
cd cmake-build-release
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

## Executables

### inspect_Norm

Print the details of the `Norm` instance.

Usage:

```bash
$ ./inspect_Norm AllC
Norm: 0xffccf 1047759 : AllC
(G->G):cGG:GG	(G->B):cGG:BB	(B->G):cGG:GG	(B->B):cGG:BB
(G->G): P:1.000 : R1 (c:1.000,d:1.000) : R2 (c:1.000,d:1.000)
(G->B): P:1.000 : R1 (c:1.000,d:1.000) : R2 (c:0.000,d:0.000)
(B->G): P:1.000 : R1 (c:1.000,d:1.000) : R2 (c:1.000,d:1.000)
(B->B): P:1.000 : R1 (c:1.000,d:1.000) : R2 (c:0.000,d:0.000)
Serialized: 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00
```

Named norms are AllC, AllD, AllG, AllB, ImageScoring, L1, L2, L3, L4, L5, L6, L7, L8, and SecondarySixteen(S1-S16).

For other norms, you can specify the norm as a string having 20 floating-point numbers separated by spaces.

```bash
$ ./inspect_Norm '1 0 1 0  1.0 0.9 0.8 0.7 0.6 0.5 0.4 0.3  1 0 1 0 1 0 1 0'
(G->G): P:1.000 : R1 (c:1.000,d:0.900) : R2 (c:1.000,d:0.000)
(G->B): P:0.000 : R1 (c:0.800,d:0.700) : R2 (c:1.000,d:0.000)
(B->G): P:1.000 : R1 (c:0.600,d:0.500) : R2 (c:1.000,d:0.000)
(B->B): P:0.000 : R1 (c:0.400,d:0.300) : R2 (c:1.000,d:0.000)
Serialized: 1.00 0.00 1.00 0.00 1.00 0.90 0.80 0.70 0.60 0.50 0.40 0.30 1.00 0.00 1.00 0.00 1.00 0.00 1.00 0.00
```

### inspect_PublicRepGame

Print the details of the Norm under public assessment model.

```bash
$ ./cmake-build-release/inspect_PublicRepGame L3
(G->G): P:0.999 : R1 (c:0.999,d:0.001) : R2 (c:0.999,d:0.999)
(G->B): P:0.000 : R1 (c:0.999,d:0.999) : R2 (c:0.001,d:0.001)
(B->G): P:0.999 : R1 (c:0.999,d:0.001) : R2 (c:0.999,d:0.999)
(B->B): P:0.000 : R1 (c:0.999,d:0.999) : R2 (c:0.001,d:0.001)
Serialized: 1.00 0.00 1.00 0.00 1.00 0.00 1.00 1.00 1.00 0.00 1.00 1.00 1.00 1.00 0.00 0.00 1.00 1.00 0.00 0.00
h*: 0.997011, pc_res_res: 0.996014
stable benefit range against ALLD: 1.00501, 1.79769e+308
stable benefit range against ALLC: 1.00501, 1.79769e+308
ESS b_range: 1.00501, 1.79769e+308
```

### inspect_PrivRepGame

Print the details of the Norm under private assessment model.
The first argument is the name of the Norm, and the number of the players.
After showing the time series of the cooperation level, the system-wide cooperation level is printed.

```bash
$ ./cmake-build-release/inspect_PrivRepGame L3 50
Parameters:
{
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000.0,
  "t_measure": 1000.0
}
20 0.907
40 0.897
60 0.898333
...
...
960 0.900396
980 0.90002
1000 0.90032
SystemWideCooperationLevel: 0.90158
Elapsed time: 0.0593253 s
```

We can simulate the population with mixed strategies. For instance, the population of 30 L1 and 30 L2 players can be simulated as follows:
The first column of the time series is the system-wide cooperation level, and the remaining columns are the cooperation probabilities between the players of each Norm.

```bash
./cmake-build-release/inspect_PrivRepGame L1 30 L2 30
Parameters:
{
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000.0,
  "t_measure": 1000.0
}
20 0.818333 0.919463 0.827815 0.768212 0.758389
40 0.798333 0.907666 0.797125 0.769968 0.721254
60 0.796944 0.904094 0.802116 0.766138 0.718129
...
...
960 0.790833 0.891011 0.791552 0.766827 0.714466
980 0.790748 0.890602 0.791529 0.766521 0.714905
1000 0.79085 0.89104 0.791409 0.766109 0.715423
SystemWideCooperationLevel: 0.78405
NormCooperationLevels:
 0.887342 0.786161
 0.757679 0.705684
Elapsed time: 0.0938164 s
```

In this example, L1 cooperates with L1 with 0.887342, L1 cooperates with L2 with 0.786161, L2 cooperates with L1 with 0.757679, and L2 cooperates with L2 with 0.705684.

You can change the simulation parameters by specifying a JSON file with the `-j` option.

```bash
./cmake-build-release/inspect_PrivRepGame -j '{"mu_assess1": 0.05, "t_init":10000, "t_measure": 10000}' L1 30 L2 30

Parameters:
{
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 10000,
  "t_measure": 10000
}
...
```

### inspect_EvolPrivRepGame

Print the fixation probabilities between two Norms under the private assessment model.

```bash
$ ./cmake-build-release/inspect_EvolPrivRepGame L1 L2
Running with 32 threads
Parameteres:{
  "N": 30,
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000,
  "t_measure": 1000
}
benefit: 5
beta: 1
Transition probabilities between L1 vs L2
  ---> : 8.67603e-05
  <--- : 0.157517
Equilibrium population: 0.99945 , 0.000550495
Monomorphic cooperation levels: 0.899233 , 0.7011
# num mutants l, pi_i[l], pi_j[l]
1 3.57338 3.148
2 3.57786 3.234
3 3.54307 3.21633
4 3.5215 3.12425
5 3.52 3.1696
6 3.49371 3.15783
7 3.45413 3.17929
8 3.44555 3.11475
9 3.47562 3.11644
10 3.38905 3.0971
11 3.38726 3.09
12 3.35706 3.07175
13 3.33488 3.09715
14 3.3115 3.026
15 3.27853 3.0452
16 3.25386 3.02613
17 3.25877 3.00847
18 3.20633 2.96289
19 3.22418 2.96432
20 3.1989 2.94075
21 3.12533 2.92857
22 3.1475 2.95
23 3.12 2.89339
24 3.06417 2.94529
25 3.028 2.8688
26 3.02 2.88138
27 3.07733 2.864
28 2.9545 2.84711
29 2.983 2.85203
Elapsed time: 0.121665 s
```

In the above example, the transition probability from L1 to L2 is `8.67603e-05` while the transition probability from L2 to L1 is `0.157517`.
The equilibrium population is `0.99945` for L1 and `0.000550495` for L2, indicating that L1 is the dominant strategy in this case.

You can change the simulation parameters by specifying a JSON file with the `-j` option.

## Tests

Unit tests are prepared. The executables that starts with `test_` are the unit tests. Run these tests using `ctest` command.

```bash
cd cmake-build-debug
ctest
```
