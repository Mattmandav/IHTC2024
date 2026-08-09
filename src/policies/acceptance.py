import math
import time
import random

"""
These acceptance procedures always take a pool of solutions and return ordered list of kept solutions.
If a solution is not accepted, a None value is put in its place and value is set to +infinity.
"""


def improve_only(values, new_solutions, best_value):
    """
    Takes values of solutions and the new solutions,
    if solution better than best it is kept going forward
    """
    solution_pool = []
    new_values = []
    for i in range(len(values)):
        # Solution is better than current best
        if values[i]["Cost"] < best_value:
            solution_pool.append(new_solutions[i])
            new_values.append(values[i]["Cost"])
        # Solution is not
        else:
            solution_pool.append(None)
            new_values.append(float("inf"))
    # Return the modified solution pool
    return solution_pool, new_values


def bestrr(values, new_solutions, best_value, rho=0.01):
    """
    Takes values of solutions and the new solutions,
    if solution better than best it is kept going forward
    """
    solution_pool = []
    new_values = []
    for i in range(len(values)):
        # Solution is better than current best + some cost
        if values[i]["Cost"] < (best_value + rho * best_value):
            solution_pool.append(new_solutions[i])
            new_values.append(values[i]["Cost"])
            """if self.verbose:
                self.hits['successful'] += 1
                self.hits['type'].append(temp_best['operator'])
                self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)"""
        # Acceptance criteria not met
        else:
            solution_pool.append(None)
            new_values.append(float("inf"))
    # Return the modified solution pool
    return solution_pool, new_values


def simulated_annealing(
    values, new_solutions, previous_values, start_time, time_limit, delta=1
):
    """
    Compares with the previous solution and uses difference in quality and time left for acceptance.
    """
    solution_pool = []
    new_values = []
    for i in range(len(values)):
        # Calculate elements of the probability
        evaluation_time = time.time() - start_time
        delta_f = max(values[i]["Cost"] - previous_values[i], 0)
        temp = delta * (1 - (evaluation_time / time_limit))
        # Try and find probability value
        try:
            p = math.exp(-(delta_f / temp))
        except OverflowError:
            p = -float("inf")
        # Roll dice for number or p == 1
        if random.random() < p or p == 1:
            solution_pool.append(new_solutions[i])
            new_values.append(values[i]["Cost"])
        # Acceptance criteria not met
        else:
            solution_pool.append(None)
            new_values.append(float("inf"))
    # Return the modified solution pool
    return solution_pool, new_values
