import json
import subprocess
import time
import multiprocessing as mp
import numpy as np
import random as rd
import tempfile
import pickle

import src.optimise.heuristics as llh
import src.optimise.greedy as grd
from src.data.instance import Data

# Main optimisation function
def main(input_file, seed = 982032024, time_limit = 60, time_tolerance = 5, verbose = False):
    # Starting function timer
    time_start = time.time()

    # Open and read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Set seed for optimisation
    rd.seed(seed)

    # Put the data into the optimiser class
    optimisation_object = Optimiser(data,
                                    instance_file_name = input_file,
                                    time_limit = time_limit,
                                    time_tolerance = time_tolerance,
                                    verbose = verbose)

    # Run an optimisation method
    solution = optimisation_object.optimise(method = "greedy")
    solution, costs = optimisation_object.improvement_hyper_heuristic(solution)
    print(optimisation_object.solution_check(solution))
    if verbose:
        pickle.dump(optimisation_object.hits, open("hits.pkl", "wb"))
            

    # Reporting process
    print(f"Main function completed in {round(time.time() - time_start,2)} seconds!")
    print()

    return solution, costs

# Optimisation class
class Optimiser():
    def __init__(self, raw_data, instance_file_name, time_limit = 60, time_tolerance = 5, verbose = False):
        # Get number of successful improvements over all iterations
        
        self.verbose = verbose


        # If logging we will record the hits and successes over time
        if self.verbose:
            # For logging purposes
            self.hits = {'tried': 0, 'successful': 0, 'type': ['None'], 'Cost Reduction': [0]}

        self.instance_file_name = instance_file_name
        # Importing low level heuristics
        self.llh_names = [name for name in dir(llh) if
                          callable(getattr(llh,name)) and
                          not name.startswith("__")
                          ]

        # Key values for optimiser
        self.cores = 4
        self.remaining_time = time_limit
        self.time_start = time.time()
        self.time_tolerance = time_tolerance

        # Processing instance data
        self.raw_data = raw_data
        self.data = Data(raw_data)

        # Info on collecting cost info
        self.costs = {"RoomAgeMix": [],
                      "RoomSkillLevel": [],
                      "ContinuityOfCare": [],
                      "ExcessiveNurseWorkload": [],
                      "OpenOperatingTheater": [],
                      "SurgeonTransfer": [],
                      "PatientDelay": [],
                      "ElectiveUnscheduledPatients": []}

        # Initial remaining time
        self.remaining_time = self.remaining_time - (time.time() - self.time_start)


    """
    Solution checking
    """

    def solution_check(self, solution):
        # Check solution
        violations = 0
        cost = 0
        reasons = []
        with tempfile.NamedTemporaryFile() as solution_file:
            solution_file.write(json.dumps(solution).encode())
            solution_file.seek(0) # Not sure what this does (hard to find documentation) but makes it run quicker
            result = subprocess.run(
                ['./bin/IHTP_Validator', self.instance_file_name, solution_file.name],
                capture_output = True, # Python >= 3.7 only
                text = True # Python >= 3.7 only
                )
        for line in result.stdout.splitlines():
            if("." in line and len(line.split()) == 1):
                if(int(line.split(".")[-1]) != 0):
                    reasons.append(line.split(".")[0])
            # Get violations
            if("Total violations" in line):
                violations = int(line.split()[-1])
            # Get cost
            if("Total cost" in line):
                cost = int(line.split()[-1])
        # Return violations and cost
        return {"Violations": violations, "Cost": cost, "Reasons": reasons}

    
    def solution_collect_costs(self, solution):

        with tempfile.NamedTemporaryFile() as solution_file:
            solution_file.write(json.dumps(solution).encode())
            solution_file.seek(0) # Not sure what this does (hard to find documentation) but makes it run quicker
            result = subprocess.run(
                ['./bin/IHTP_Validator', self.instance_file_name, solution_file.name],
                capture_output = True, # Python >= 3.7 only
                text = True # Python >= 3.7 only
                )
        for line in result.stdout.splitlines():
            if('(' in line and '.' in line):
                self.costs[line.split('.')[0]].append(float(line.split('.')[-1].split()[0]))
                
    def solution_score(self, solution):
        values = self.solution_check(solution)
        if(values["Violations"] > 0):
            values["Cost"] = np.inf
            return values
        else:
            return values


    """
    Optimisation functions
    """

    def optimise(self, method = None):
        # Don't apply method
        if(method == None):
            print("Methods coming soon!")
            solution = {"patients": [], "nurses": []}
        # Apply greedy heuristic
        elif(method == "greedy"):
            t0 = time.time()
            [solution, self.remaining_time] = grd.greedy_allocation(self,self.data)
            print("Greedy approach took {} seconds".format(time.time()-t0))
        # Method doesn't exist
        else:
            solution = {"patients": [], "nurses": []}
        # Returning the solution
        return solution


    """
    Hyper-heurisic improvement
    """
    
    def improvement_hyper_heuristic(self, solution, pool_size = 4):
        """
        The improvement heuristic applies 4 moves at the same time to the current solution.
        It will never accept an infeasible solution.
        If we have multiple feasible the "best" solution has a chance of being selected as current.
        100% chance if solution is improving or equivalent.
        p% chance if the solution is not improving.
        The best solution is always saved.
        """
        # Checking if we have time to improve solution
        if(self.remaining_time <= self.time_tolerance):
            return solution
        
        # Preallocating features
        print(f"Starting hyper-heuristic (Remaining time: {round(self.remaining_time,2)} seconds)")
        best_solution = solution
        best_solution_value = self.solution_check(solution)["Cost"]
        current_solution = solution
        current_solution_value = best_solution_value
        
        # Applying heuristic
        while self.remaining_time > self.time_tolerance:
            # Timing iteration
            time_start = time.time()

            # Making copies of solution
            solution_pool = []
            for p in range(pool_size):
                solution_pool.append(current_solution)

            # Applying moves
            with mp.Pool(self.cores) as p:
                # Since map is ordered we don't need to worry about which solution is which
                new_solutions = p.map(self.solution_adjustment,solution_pool)      
                values = p.map(self.solution_score,new_solutions)

            # Append number of attempts
            if self.verbose:
                self.hits['tried'] += 1

            # Selecting best solution of this pool
            temp_best_index = np.argmin([value['Cost'] for value in values])
            temp_best =  new_solutions[temp_best_index] # This is the json for the temp_best solution

            # Record costs and violations
            temp_best_value = values[temp_best_index]['Cost']
            temp_best_violations = values[temp_best_index]["Violations"]

            # Checking that the best solution is feasible
            if(temp_best_violations > 0):
                continue

            # Saving best solution
            if(temp_best_value < best_solution_value):
                
                best_solution = temp_best
                best_solution_value = temp_best_value

                # Dont quite get the point of this (?)
                # Assume its just collecting costs over time but why don't you just collect all this information from the start when running the intiial pool instead of at the end?
                # Also since its for plotting, we'll only do this is the plotting option is chosen
                if self.verbose:
                    # Save costs data
                    self.solution_collect_costs(temp_best)

            # Deciding whether to accept new solution as current solution
            if(temp_best_value < current_solution_value):
                if self.verbose:
                    self.hits['successful'] += 1
                    self.hits['type'].append(temp_best['operator'])
                    self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)
                current_solution = temp_best
                current_solution_value = temp_best_value
                
            # Updating the time remaining
            self.remaining_time = self.remaining_time - (time.time() - time_start)
            if self.verbose:
                print("Loops ran: {}, successes: {}, successful operators: {}".format(self.hits['tried'],self.hits['successful'],max(set(self.hits['type']), key=self.hits['type'].count)))
        # Return the best solution
        return best_solution, self.costs

    
    def solution_adjustment(self,solution):
        """
        Takes self and solution as input, applies an operator and returns new solution.
        """

        # Select an operator from the llh package to use
        operator_name = rd.choices(self.llh_names)[0]
        new_solution = eval("llh."+operator_name+"(self.data,solution)")
        
        # Add the operator used
        new_solution['operator'] = operator_name
        # Return final solution
        return new_solution