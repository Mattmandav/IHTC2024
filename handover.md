# IHTC2024 Handover

## Project overview

The main files you need to care about are:

- `main.py`
  - Best for running one specific instance with command-line parameters.
  - Parses command-line arguments.
  - Builds the input/output paths.
  - Calls `src.optimise.optimiser.main(...)`.
  - Saves the generated solution JSON.
  - Optionally saves costs and plots objective values.

- `run_public.py`
  - One of the main files to use for full public-instance runs.
  - Runs public instances `i01.json` to `i30.json` from `data/instances`.
  - Loops over the tuned configurations in its `params` dictionary.
  - Currently runs `random`, `qlearner`, and `mcrl` with `sa` acceptance.
  - Calls `src.optimise.optimiser.main(...)` directly with `time_limit=600`, `time_tolerance=3`, and `seed=42`.
  - Writes files named like `instance_{selection}_{acceptance}_sol_{instance}` into the output directory passed as the first argument.

- `run_hidden.py`
  - One of the main files to use for full hidden-instance style runs.
  - Same structure as `run_public.py`, but runs hidden-style instances `m01.json` to `m30.json`.
  - Uses the same tuned `params` dictionary structure as `run_public.py`.
  - Currently runs `random`, `qlearner`, and `mcrl` with `sa` acceptance.
  - Calls `src.optimise.optimiser.main(...)` directly with `time_limit=600`, `time_tolerance=3`, and `seed=42`.
  - Writes files named like `instance_{selection}_{acceptance}_sol_{instance}` into the output directory passed as the first argument.

- `src/optimise/optimiser.py`
  - Function: `main(...)`
  - Class: `Optimiser`
  - Loads the instance JSON, builds an `Optimiser`, creates an initial greedy solution, and optionally improves it using a hyper-heuristic.

- Don't worry about `bulk_main.py`

## Environment setup

The project uses Python `>=3.12`, defined in `pyproject.toml`.

Dependencies you need are within the `pyproject.toml` and include:

- `numpy`
- `pandas`
- `plotly`
- `ruff`
- `irace` <- note irace can be a bit tricky as you need it in R as well on your linux distro. Also might not work easily on storm.

We use `uv`, to run the code, which is a python project management tool. Its super easy to install and use. 

Setup (install packages):

```bash
uv sync
```

## Running a single instance

The main entry point is `main.py`.

Basic example:

```bash
python main.py i01.json
```

By default this reads from:

```text
data/instances/i01.json
```

and writes to:

```text
data/solutions/sol_i01.json
```

Example using random selection:

```bash
python main.py i01.json --selection=random
```

Example using Q-learning selection and verbose output:

```bash
python main.py i01.json --selection=qlearner --verbose
```

Example with explicit folders:

```bash
python main.py i01.json \
  --input_folder data/instances \
  --output_folder data/solutions
```

Example competition-style run:

```bash
python main.py i01.json \
  --input_folder data/instances \
  --output_folder data/solutions \
  --time_limit 600 \
  --time_tolerance 5 \
  --selection qlearner \
  --acceptance sa \
  --sequence_length 2 \
  --num_cores 4
```

## `main.py` parameters

Defined in `main.py`.

### Positional arguments

| Parameter | Type | Required | Description |
|---|---:|---:|---|
| `input_file` | `str` | yes | Instance filename, usually something like `i01.json`. Combined with `--input_folder` unless `--input_folder` is empty. |

### Optional arguments

| Parameter | Type | Default | Choices | Description |
|---|---:|---:|---|---|
| `--seed` | `int` | `42` | any int | Random seed passed to `src.optimise.optimiser.main(...)`. |
| `--input_folder` | `str` | `data/instances` | path | Folder containing input instance JSON files. |
| `--output_folder` | `str` | `data/solutions` | path | Folder where solution JSON files are written. Must already exist. |
| `--time_limit` | `float` | `600` | any float | Optimisation time limit in seconds. |
| `--time_tolerance` | `float` | `5` | any float | Safety buffer subtracted from effective run time. |
| `--plot` | flag | off | — | Calls `src.utils.plotter.plot_objectives(...)` after the run. |
| `--verbose` | flag | off | — | Enables verbose optimiser behaviour. In `src.optimise.optimiser.main(...)`, verbose mode also writes debug hits to `debug/hits.pkl`. |
| `--selection` | `str` | `random` | `qlearner`, `random`, `mcrl`, `none` | Hyper-heuristic selection policy. |
| `--acceptance` | `str` | `sa` | `improve_only`, `r2r`, `sa`, `none` | Acceptance criterion. |
| `--sequence_length` | `int` | `0` | any int | Number of low-level heuristic moves selected per sequence. If `0`, `main.py` sets this automatically based on `--selection`. |
| `--save_costs` | flag | off | — | Saves individual cost history as CSV. |
| `--costs_folder` | `str` | `data/individual_costs` | path | Folder for cost CSV files. Must already exist if `--save_costs` is used. |
| `--lambda_qlearner` | `float` | `0.00005` | any float | Learning parameter passed as `lambda_q` to `src.optimise.optimiser.main(...)`. |
| `--rho_learning_rate` | `float` | `0.01` | any float | R2R learning/rate parameter passed as `rho_r2r`. |
| `--num_cores` | `int` | `4` | any int | Number of cores used by the improvement hyper-heuristic. |
| `--delta_sa` | `float` | `1` | any float | Simulated annealing delta parameter. |

## Automatic `sequence_length` behaviour

In `main.py`, if `--sequence_length` is left as `0`, it is changed based on `--selection`:

| `--selection` | automatic `sequence_length` |
|---|---:|
| `random` | `1` |
| `qlearner` | `4` |
| `mcrl` | `4` |
| `none` | `0` |

## Selection policies

The allowed `--selection` values in `main.py` are:

```text
qlearner
random
mcrl
none
```

These are passed into `src.optimise.optimiser.main(...)` as `heuristic_selection`.

If `heuristic_selection != "none"`, `src.optimise.optimiser.main(...)` calls:

```text
Optimiser.improvement_hyper_heuristic(...)
```

If `heuristic_selection == "none"`, the optimiser only collects costs for the greedy solution.

## Acceptance policies

The allowed `--acceptance` values in `main.py` are:

```text
improve_only
r2r
sa
none
```

These are passed into `src.optimise.optimiser.main(...)` as `acceptance_selection`.

## Output files

`main.py` writes solution files using this pattern:

```text
{output_folder}/sol_{input_filename_without_json}.json
```

For example:

```bash
python main.py i01.json
```

writes:

```text
data/solutions/sol_i01.json
```

If `--save_costs` is used, `main.py` writes a CSV to `--costs_folder` using this pattern:

```text
{first_three_chars_of_input_file}_{selection}_{acceptance}.csv
```

For example:

```text
i01_qlearner_sa.csv
```

## Bash / Slurm scripts

The repository includes several Slurm bash scripts for cluster runs.

These scripts generally:

1. Set Slurm job options.
2. Create an output directory.
3. Run a Python runner with `uv run`.

Below are a couple of examples you can use to get the idea of different types

### Public 10-minute runs (example)

File: `run_public_10_mins.sh`

Key settings:

```bash
#SBATCH -c 4
#SBATCH --array=1-20
```

It creates a directory based on the Slurm array task ID:

```bash
DIRECTORY='./data/solutions/run'$SLURM_ARRAY_TASK_ID
```

Then runs:

```bash
srun uv run ~/IHTC2024_R2/run_public.py $DIRECTORY
```

The Python script `run_public.py` runs public instances `i01.json` to `i30.json`.

Inside `run_public.py`, the active configuration loops over:

```text
selection: random, qlearner, mcrl
acceptance: sa
time_limit: 600
time_tolerance: 3
seed: 42
```

The tuned parameter examples in `run_public.py` are:

| Selection | Acceptance | Parameters |
|---|---|---|
| `random` | `sa` | `sequence_length=1`, `delta_sa=1000` |
| `qlearner` | `sa` | `sequence_length=2`, `delta_sa=1`, `lambda_q=0.002555141214583` |
| `mcrl` | `sa` | `sequence_length=1`, `delta_sa=100`, `lambda_q=0.002392316742348` |

### Public 1-core runs

File: `run_public_1_cores.sh`

Key settings:

```bash
#SBATCH -c 1
#SBATCH --array=1-20
```

It runs:

```bash
srun uv run ~/IHTC2024_R2/run_public_1_core.py $DIRECTORY
```

`run_public_1_core.py` is a variant of the public runner intended for 1-core Slurm jobs.

### Save-over-time runs

File: `run_save_over_time.sh`

Key settings:

```bash
#SBATCH -c 4
#SBATCH --array=1-30%25
```

It writes to:

```bash
DIRECTORY='./data/solutions/solutions_over_time'
```

Then runs:

```bash
srun uv run ~/IHTC2024_R2/run_save_over_time.py $DIRECTORY $SLURM_ARRAY_TASK_ID
```

`run_save_over_time.py` expects:

```text
1. output directory
2. public instance index
```

It calls `src.optimise.optimiser.main(...)` with:

```text
time_limit=7200
time_tolerance=3
save_improvement_over_time=True
```

## Validator

The validator binary is expected at:

```text
./bin/IHTP_Validator
```


There is also a `Makefile`, but it refers to:

```text
.IHTP_Validator.cc
```

and target:

```text
.IHTP_Validator
```

whereas the Python code expects:

```text
./bin/IHTP_Validator
```

So validation is normally run using the existing binary in `bin`. or you can rebuild and put it in `bin`

## Recommended common commands

### Run one instance quickly

```bash
uv run python main.py i01.json --time_limit 60 --time_tolerance 5
```

### Run one instance with Q-learner and simulated annealing

```bash
uv run python main.py i01.json \
  --selection qlearner \
  --acceptance sa \
  --sequence_length 2 \
  --lambda_qlearner 0.002555141214583 \
  --delta_sa 1 \
  --time_limit 600 \
  --time_tolerance 3
```

## Notes and gotchas

- `main.py` requires the output folder to already exist.
- `main.py` raises `ValueError("Invalid input file/folder")` if the instance path cannot be found.
- `main.py` raises `ValueError("Invalid output folder")` if the output folder does not exist.
- Several Slurm scripts contain absolute home-directory paths such as:
  - `~/IHTC2024_R2/run_public.py`
  - `~/IHTC2024_R2/run_supplementary.py`
- If running on another machine, update those paths or run the Python scripts directly from the repository root.
- `run_supplementary.py` and `run_save_over_time.py` use `sys.argv[2]` as an index, so they require both an output directory and an index argument.
- `run_public.py` and `run_hidden.py` run many instances/configurations in one invocation, so they can take a long time.