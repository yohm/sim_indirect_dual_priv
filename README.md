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
git clone --recursive git@github.com:yohm/sim_indirect_dual_priv.git
cd sim_indirect_dual_priv
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

Prints private-assessment dynamics. Logs (parameters, warm-up series, elapsed) go to stderr; structured results are printed as JSON to stdout.

Usage:

```bash
./cmake-build-release/inspect_PrivRepGame [-j <param.json|json-string>] [-g] <Norm1> <n1> [<Norm2> <n2> ...]
```

```bash
$ ./cmake-build-release/inspect_PrivRepGame L3 50
# stderr
Parameters:
{
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000,
  "t_measure": 1000
}
20 0.907
40 0.897
...
1000 0.90032
Elapsed time: 0.059 s

# stdout
{
  "SystemWideCooperationLevel": 0.90158
}
```

We can simulate the population with mixed strategies. For instance, the population of 30 L1 and 30 L2 players can be simulated as follows:
The first column of the time series is the system-wide cooperation level, and the remaining columns are the cooperation probabilities between the players of each Norm.

```bash
./cmake-build-release/inspect_PrivRepGame L1 30 L2 30
# stderr (truncated)
Parameters:
{
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000,
  "t_measure": 1000
}
20 0.818333 0.919463 0.827815 0.768212 0.758389
40 0.798333 0.907666 0.797125 0.769968 0.721254
...
1000 0.79085 0.89104 0.791409 0.766109 0.715423
Elapsed time: 0.094 s

# stdout
{
  "SystemWideCooperationLevel": 0.78405,
  "NormCooperationLevels": [
    [0.887342, 0.786161],
    [0.757679, 0.705684]
  ]
}
```

In this example, L1 cooperates with L1 with 0.887342, L1 cooperates with L2 with 0.786161, L2 cooperates with L1 with 0.757679, and L2 cooperates with L2 with 0.705684.

You can change the simulation parameters by specifying a JSON file with the `-j` option.

```bash
./cmake-build-release/inspect_PrivRepGame -j '{"mu_assess1":0.05,"t_init":10000,"t_measure":10000}' L1 30 L2 30
```

### inspect_EvolPrivRepGame

Computes evolutionary outcomes under private assessment.

Usage:

```bash
./cmake-build-release/inspect_EvolPrivRepGame [-j <param.json|json-string>] <Norm>
./cmake-build-release/inspect_EvolPrivRepGame [-j <param.json|json-string>] <Norm1> <Norm2>
```

Notes:

- Logs (threads, parameters, elapsed) go to stderr. Results are printed as JSON to stdout.
- With one norm, returns selection–mutation equilibrium against AllC/AllD: `self_cooperation_level`, `rhos`, `eq`, and `eq_cooperation_level`.
- With two norms, returns transition probabilities, low-mutation equilibrium population, and monomorphic cooperation levels. Also writes `payoffs.dat` (columns: `l pi_norm1[l] pi_norm2[l]`).

Two-norm example:

```bash
$ ./cmake-build-release/inspect_EvolPrivRepGame L1 L2
# stderr
Running with 32 threads
Parameters:{
  "N": 30,
  "mu_assess1": 0.05,
  "mu_assess2": 0.0,
  "mu_impl": 0.0,
  "mu_percept": 0.0,
  "q": 1.0,
  "seed": 123456789,
  "t_init": 1000,
  "t_measure": 1000,
  "benefit": 5,
  "beta": 1
}
Elapsed time: 0.12 s

# stdout
{
  "transition_prob:n1->n2": 8.67603e-05,
  "transition_prob:n1<-n2": 0.157517,
  "equilibrium_population": [0.99945, 0.000550495],
  "monomorphic_coop_levels": [0.899233, 0.7011]
}
```

Single-norm example:

```bash
$ ./cmake-build-release/inspect_EvolPrivRepGame L3
# stdout
{
  "self_cooperation_level": 0.90,
  "rhos": [ ... ],
  "eq": [ ... ],
  "eq_cooperation_level": 0.90
}
```

## Python Scripts and Environment (uv)

This repository includes Python helper scripts under `script/` for analysis and plotting. They depend only on NumPy and Matplotlib and interact with the built C++ executables.

### Environment setup with uv

- Install uv (package manager by Astral) if you don't have it:
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows (PowerShell): `irm https://astral.sh/uv/install.ps1 | iex`

From the repository root:

```bash
uv venv .venv
source .venv/bin/activate              # Windows: .venv\\Scripts\\Activate.ps1
uv pip install -r script/requirements.txt
```

Build the C++ executables (Release) if you plan to use the inspection/triadic scripts:

```bash
cmake -S . -B cmake-build-release -DCMAKE_BUILD_TYPE=Release
cmake --build cmake-build-release -j
```

### How to run the scripts

- Image matrix simulation/plot (no C++ dependency):
  - `python script/ImageMatrix.py --norm L3 --N 50 --ep 0.05 --q 0.9 --nIt 20000 --seed 0`
  - `python script/ImageMatrix.py --norm all`

- Norm comparisons (requires built executables):
  - `python script/compare_Norm.py`

- Triadic competition plot (requires built executables):
  - `python script/TriadicCompetition.py L1`
  - or pass a full parameter string: `python script/TriadicCompetition.py "1.00 0.00 ..."`

## Tests

Unit tests are prepared. The executables that starts with `test_` are the unit tests. Run these tests using `ctest` command.

```bash
cd cmake-build-debug
ctest
```
