import subprocess
import os
from irace import irace, ParameterSpace, Integer, Scenario, Real
import pandas as pd
import sys


def target_runner_ql_sa(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "qlearner",
        "--acceptance",
        "sa",
        "--lambda_qlearner",
        str(lambda_q),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_ql_improve_only(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "qlearner",
        "--acceptance",
        "improve_only",
        "--lambda_qlearner",
        str(lambda_q),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_ql_r2r(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]
    rho = experiment.configuration["rho"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "qlearner",
        "--acceptance",
        "r2r",
        "--lambda_qlearner",
        str(lambda_q),
        "--rho_learning_rate",
        str(rho),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_mcrl_improve_only(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "mcrl",
        "--acceptance",
        "improve_only",
        "--lambda_qlearner",
        str(lambda_q),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_mcrl_r2r(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]
    rho = experiment.configuration["rho"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "mcrl",
        "--acceptance",
        "r2r",
        "--lambda_qlearner",
        str(lambda_q),
        "--rho_learning_rate",
        str(rho),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_mcrl_sa(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    lambda_q = experiment.configuration["lambda_qlearner"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "mcrl",
        "--acceptance",
        "sa",
        "--lambda_qlearner",
        str(lambda_q),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_random_sa(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "random",
        "--acceptance",
        "sa",
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_random_r2r(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]
    rho = experiment.configuration["rho"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "random",
        "--acceptance",
        "r2r",
        "--rho_learning_rate",
        str(rho),
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def target_runner_random_improve_only(experiment, scenario):
    """
    This function is called by irace for every test.
    It runs the IHTC solver and returns the cost.
    """
    # configuration is a dict, e.g., {'sequence_length': 20}
    seq_len = experiment.configuration["sequence_length"]

    # Construct the command to run your solver
    # instance is the path to the JSON file provided by irace
    command = [
        "uv",
        "run",
        "main.py",
        "--sequence_length",
        str(seq_len),
        "--seed",
        str(experiment.seed),
        "--time_limit",
        str(600),
        "--selection",
        "random",
        "--acceptance",
        "improve_only",
        str(experiment.instance),
    ]

    try:
        # Run the solver and capture output
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result)
        # Get the last line of output (the cost)
        lines = result.stdout.strip().split("\n")
        cost = float(lines[-1])
        return cost
    except Exception as e:
        print(f"Error running instance {experiment.instance}: {e}")
        return 999999.0  # Return a very high cost on failure


def main(parameter_space_to_run, method_to_run, method_id):
    # 1. Define the Parameter Space
    # name, type ('i' for integer, 'r' for real, 'c' for categorical), range/values
    ps = parameter_space_to_run

    # 2. Get list of instances (JSON files in the data/instances folder)
    instance_dir = "data/instances"

    scenario = Scenario(
        max_experiments=300,
        instances=[f for f in os.listdir(instance_dir) if f.endswith(".json")],
        verbose=0,
        seed=42,
    )
    # 3. Initialize iracepy-tiny
    # max_experiments: total number of times the solver will be run
    irace_eg = irace(
        target_runner=method_to_run,
        parameter_space=ps,
        scenario=scenario,
        return_df=True,
    )

    # 4. Run the tuning
    print("Starting tuning...")
    irace_eg.to_csv("./{}.csv".format(method_id))
    print(irace_eg)


if __name__ == "__main__":
    run = int(sys.argv[1])
    if run == 1:
        main(
            ParameterSpace(
                [Integer("sequence_length", 1, 7), Real("lambda_qlearner", 0, 0.005)]
            ),
            target_runner_ql_sa,
            "QL_sa",
        )
    elif run == 2:
        main(
            ParameterSpace(
                [Integer("sequence_length", 1, 7), Real("lambda_qlearner", 0, 0.005)]
            ),
            target_runner_ql_improve_only,
            "QL_io",
        )
    elif run == 3:
        main(
            ParameterSpace(
                [Integer("sequence_length", 1, 7), Real("lambda_qlearner", 0, 0.005)]
            ),
            target_runner_mcrl_improve_only,
            "mcrl_io",
        )
    elif run == 4:
        main(
            ParameterSpace(
                [Integer("sequence_length", 1, 7), Real("lambda_qlearner", 0, 0.005)]
            ),
            target_runner_mcrl_sa,
            "mcrl_sa",
        )
    elif run == 5:
        main(
            ParameterSpace([Integer("sequence_length", 1, 7)]),
            target_runner_random_sa,
            "r_sa",
        )
    elif run == 6:
        main(
            ParameterSpace([Integer("sequence_length", 1, 7)]),
            target_runner_random_improve_only,
            "r_io",
        )
    elif run == 7:
        main(
            ParameterSpace([Integer("sequence_length", 1, 7), Real("rho", 0, 1)]),
            target_runner_random_r2r,
            "r_r2r",
        )
    elif run == 8:
        main(
            ParameterSpace(
                [
                    Integer("sequence_length", 1, 7),
                    Real("lambda_qlearner", 0, 0.005),
                    Real("rho", 0, 1),
                ]
            ),
            target_runner_ql_r2r,
            "QL_r2r",
        )
    else:
        main(
            ParameterSpace(
                [
                    Integer("sequence_length", 1, 7),
                    Real("lambda_qlearner", 0, 0.005),
                    Real("rho", 0, 1),
                ]
            ),
            target_runner_mcrl_r2r,
            "mcrl_r2r",
        )
