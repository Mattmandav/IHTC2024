"""
irace tuning for every (selection, acceptance, heuristic set) combination.

Usage:
    uv run irace.py              run all 27 configurations in sequence
    uv run irace.py <run>        run one configuration by number (1-27) or id
    uv run irace.py --list       show all configurations

On STORM, irace_slurm.sh runs each configuration as one task of a job array.

Runs 1-9 keep their original numbering and use our heuristics ("ours");
10-18 repeat them with the IMADA heuristics and 19-27 with both sets.
Results are written to ./<id>.csv, e.g. ./QL_sa_imada.csv.

Tuned parameters depend on the configuration:
    sequence_length   always                         (1 to 7)
    lambda_qlearner   qlearner and mcrl selection    (0 to 0.005)
    rho               r2r acceptance                 (0 to 1)
    delta_sa          sa acceptance                  (0 to 1)
"""

import os
import subprocess
import sys

from irace import Integer, ParameterSpace, Real, Scenario, irace

SELECTIONS = {"qlearner": "QL", "mcrl": "mcrl", "random": "r"}
ACCEPTANCES = {"sa": "sa", "improve_only": "io", "r2r": "r2r"}
HEURISTIC_SETS = ["ours", "imada", "both"]

# Original run order (runs 1-9), repeated for each heuristic set
RUN_ORDER = [
    ("qlearner", "sa"),
    ("qlearner", "improve_only"),
    ("mcrl", "improve_only"),
    ("mcrl", "sa"),
    ("random", "sa"),
    ("random", "improve_only"),
    ("random", "r2r"),
    ("qlearner", "r2r"),
    ("mcrl", "r2r"),
]

CONFIGURATIONS = [
    (selection, acceptance, heuristic_set)
    for heuristic_set in HEURISTIC_SETS
    for selection, acceptance in RUN_ORDER
]

TIME_LIMIT = 600
FAILED_COST = 999999.0


def method_id(selection, acceptance, heuristic_set):
    return f"{SELECTIONS[selection]}_{ACCEPTANCES[acceptance]}_{heuristic_set}"


def parameter_space(selection, acceptance):
    params = [Integer("sequence_length", 1, 7)]
    if selection in ("qlearner", "mcrl"):
        params.append(Real("lambda_qlearner", 0, 0.005))
    if acceptance == "r2r":
        params.append(Real("rho", 0, 1))
    if acceptance == "sa":
        params.append(Real("delta_sa", 0, 1))
    return ParameterSpace(params)


def build_command(selection, acceptance, heuristic_set, configuration, seed, instance):
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(configuration["sequence_length"]),
        "--seed",
        str(seed),
        "--time_limit",
        str(TIME_LIMIT),
        "--selection",
        selection,
        "--acceptance",
        acceptance,
        "--heuristic_set",
        heuristic_set,
    ]
    if "lambda_qlearner" in configuration:
        command += ["--lambda_qlearner", str(configuration["lambda_qlearner"])]
    if "rho" in configuration:
        command += ["--rho_learning_rate", str(configuration["rho"])]
    if "delta_sa" in configuration:
        command += ["--delta_sa", str(configuration["delta_sa"])]
    return command + [str(instance)]


def make_target_runner(selection, acceptance, heuristic_set):
    def target_runner(experiment, scenario):
        """
        Called by irace for every experiment: runs the IHTC solver and returns
        the cost, which main.py prints as the last line of its output.
        """
        command = build_command(
            selection,
            acceptance,
            heuristic_set,
            experiment.configuration,
            experiment.seed,
            experiment.instance,
        )
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(result)
            lines = result.stdout.strip().split("\n")
            return float(lines[-1])
        except Exception as e:
            print(f"Error running instance {experiment.instance}: {e}")
            return FAILED_COST

    return target_runner


def check_imada_bridge():
    """
    Without the compiled bridge every IMADA run would fail and score
    FAILED_COST, so irace would tune on meaningless results. Fail early instead.
    """
    try:
        import src.optimise.heuristics_imada  # noqa: F401
    except ImportError as e:
        sys.exit(f"Cannot tune with the IMADA heuristics:\n{e}")


def main(selection, acceptance, heuristic_set):
    if heuristic_set in ("imada", "both"):
        check_imada_bridge()

    instance_dir = "data/instances"
    scenario = Scenario(
        max_experiments=300,
        instances=[f for f in os.listdir(instance_dir) if f.endswith(".json")],
        verbose=0,
        seed=42,
    )

    name = method_id(selection, acceptance, heuristic_set)
    print(f"Starting tuning: {name}")
    irace_eg = irace(
        target_runner=make_target_runner(selection, acceptance, heuristic_set),
        parameter_space=parameter_space(selection, acceptance),
        scenario=scenario,
        return_df=True,
    )
    irace_eg.to_csv(f"./{name}.csv")
    print(irace_eg)


def list_configurations():
    for i, configuration in enumerate(CONFIGURATIONS, start=1):
        print(f"{i:2d}  {method_id(*configuration)}")


def parse_configuration(arg):
    ids = [method_id(*c) for c in CONFIGURATIONS]
    if arg.isdigit() and 1 <= int(arg) <= len(CONFIGURATIONS):
        return CONFIGURATIONS[int(arg) - 1]
    if arg in ids:
        return CONFIGURATIONS[ids.index(arg)]
    sys.exit(f"Unknown run '{arg}'. Use 1-{len(CONFIGURATIONS)} or one of:\n" + "\n".join(ids))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        sys.exit(__doc__)

    if len(sys.argv) == 2:
        if sys.argv[1] == "--list":
            list_configurations()
        else:
            main(*parse_configuration(sys.argv[1]))
    else:
        # No argument: run everything in sequence. Check the IMADA bridge
        # first, rather than failing when the first IMADA configuration starts.
        if any(c[2] in ("imada", "both") for c in CONFIGURATIONS):
            check_imada_bridge()
        for i, configuration in enumerate(CONFIGURATIONS, start=1):
            print(f"[{i}/{len(CONFIGURATIONS)}] {method_id(*configuration)}")
            main(*configuration)
