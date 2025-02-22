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
from src.policies import qlearner

# Main optimisation function
def main(input_file, seed = 982032024, time_limit = 60, time_tolerance = 5, verbose = False, heuristic_selection = "random", sequence_length=1):

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
                                    verbose = verbose,
                                    heuristic_selection = heuristic_selection,
                                    sequence_length=sequence_length)

    # Run an optimisation method
    solution = optimisation_object.optimise(method = "greedy")
    solution, costs = optimisation_object.improvement_hyper_heuristic(solution)
    print(optimisation_object.solution_check(solution))
    if verbose:
        pickle.dump(optimisation_object.hits, open("debug/hits.pkl", "wb"))
            

    # Reporting process
    print(f"Main function completed!")
    print()

    return solution, costs

# Optimisation class
class Optimiser():
    def __init__(self, raw_data, instance_file_name, time_limit = 60, time_tolerance = 5, verbose = False, heuristic_selection = "qlearner", sequence_length=1):
        # Get number of successful improvements over all iterations
        
        self.verbose = verbose

        self.time_limit = time_limit

        # If logging we will record the hits and successes over time
        if self.verbose:
            # For logging purposes
            self.hits = {'tried': 0, 'successful': 0, 'type': ['None'], 'Cost Reduction': [0]}
        
        self.heuristic_selection = heuristic_selection # Random or Qlearner

        self.instance_file_name = instance_file_name
        # Importing low level heuristics
        self.llh_names = [name for name in dir(llh) if
                          callable(getattr(llh,name)) and
                          not name.startswith("__")
                          ]
        if self.heuristic_selection == "qlearner":
            self.llh_names = self.llh_names+["End"]
        self.llh_dict = {}
        for name in self.llh_names:
            self.llh_dict[name] = len(self.llh_dict)

        # Key values for optimiser
        self.cores = 4
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
        
        # QLEARNING ELEMENTS
        self.max_sequence_length = sequence_length # putting one here to allow for test case to be ran
        number_of_low_level_heuristics = len(self.llh_names)
        base_learn_rate = 0.1
        discount_factor = 1
        #need self object for the qlearner agent, so this is can be called later on
        self.agent = qlearner.QLearner(
            n_states = (self.max_sequence_length,number_of_low_level_heuristics+2), #need pointers for these 2 values
            n_actions = number_of_low_level_heuristics + 2, #Plus one to signfy the action of ending the sequence of LLHs
            learn_rate = base_learn_rate,
            discount_factor = discount_factor,
            q_table = None,
            current_state = None,
            new_state = None     
        )

        #Initialise the qtable using inputs above
        #Default q_value is 0.0, set to 1.0 to be optimistic (if using 1-0 reward)
        starting_q_value = 1.0
        self.agent.initialiseQTable(q_value = starting_q_value)

        #decaying learning rate setup
        self.agent.setLearnRate(1)
        self.NVisits = np.zeros((self.max_sequence_length,number_of_low_level_heuristics+2, number_of_low_level_heuristics+2))

        #maximum exploration probability for decaying e-greedy
        self.max_explore = 1

        # maximum exploration probability for decaying e-greedy
        self.min_explore = 0.005

        # rate of decay for decaying e-greedy
        self.explore_decay_rate = 0.00005

        self.episode = 0

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
        values["Cost"] += 1000*values["Violations"]
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
            solution = grd.greedy_allocation(self,self.data)
            print("Greedy approach took {} seconds".format(time.time()-t0))
        # Method doesn't exist
        else:
            solution = {"patients": [], "nurses": []}
        # Returning the solution
        return solution


    """
    Hyper-heurisic improvemen
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
        
        # Preallocating features
        print(f"Starting hyper-heuristic")
        best_solution = solution
        best_solution_value = self.solution_check(solution)["Cost"]
        current_solution = solution
        current_solution_value = best_solution_value
        
        # Making copies of solution
        solution_pool = []
        for p in range(pool_size):
            solution_pool.append(current_solution)
        
        # Applying heuristic
        t_end = time.time() + (self.time_limit - self.time_tolerance)
        while time.time() < t_end:

            # Making copies of solution
            # solution_pool = []
            # for p in range(pool_size):
            #     solution_pool.append(current_solution)

            # Applying moves
            with mp.Pool(self.cores) as p:
                # Find which strategy selection is used
                if (self.heuristic_selection == 'random'):
                    new_solutions = p.map(self.random_solution_adjustment,solution_pool)
                elif (self.heuristic_selection == 'qlearner'):
                    new_solutions = p.map(self.qlearner_solution_adjustment,solution_pool)    
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
            
            # Saving best solution
            if(temp_best_value < best_solution_value):
                if(temp_best_violations > 0):
                   continue 
                
                best_solution = temp_best
                best_solution_value = temp_best_value

                # Dont quite get the point of this (?)
                # Assume its just collecting costs over time but why don't you just collect all this information from the start when running the intiial pool instead of at the end?
                # Also since its for plotting, we'll only do this is the plotting option is chosen
                if self.verbose:
                    # Save costs data
                    self.solution_collect_costs(temp_best)

            # Deciding whether to accept new solution as current solution
            solution_pool = []
            for i in range(len(values)):
                if(temp_best_value < current_solution_value
                   or values[i]["Cost"] < (best_solution_value + 0.01*best_solution_value)):
                        solution_pool.append(new_solutions[i])
                        if self.verbose:
                            self.hits['successful'] += 1
                            self.hits['type'].append(temp_best['operator'])
                            self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)
                            
                        current_solution = temp_best
                        current_solution_value = temp_best_value
                
            # Padding solutions
            while len(solution_pool)<pool_size:
                solution_pool.append(best_solution)

            if self.verbose:
                print("Loops ran: {}, Accepted Operators: {}, Most used operators: {}, Most Recent operator: {}".format(self.hits['tried'],self.hits['successful'],max(set(self.hits['type']), key=self.hits['type'].count),self.hits['type'][-1]))
                
        # Return the best solution
        return best_solution, self.costs

    def random_solution_adjustment(self,solution):
        """
        Takes self and solution as input, applies an operator and returns new solution.
        """

        # Select an operator from the llh package to use
        operator_names = rd.choices(self.llh_names,k=rd.randint(1,self.max_sequence_length))
        init_solution = solution

        for operator in operator_names:
            new_solution = eval("llh."+operator+"(self.data,init_solution)")
            init_solution = new_solution
        
        # Add the operator used
        new_solution['operator'] = str(operator_names)
        # Return final solution
        return new_solution

    def qlearner_solution_adjustment(self,solution):
        """
        Takes self and solution as input, applies an operator and returns new solution.
        """
        
        new_solution = solution
        number_of_low_level_heuristics = len(self.llh_names)
        self.agent.setCurrentState((0, number_of_low_level_heuristics + 1))

        #epsilon-Greedy policy for picking actions dervied from Q
        #Magic number here - can be changed and switched to a better regime
        # explore_prob = 0.1

        self.episode += 1

        # Update explore probability
        explore_prob = self.min_explore + (self.max_explore - self.min_explore)*np.exp(-self.explore_decay_rate*self.episode)

        #e.g. decaying epslion-greedy, UCB (Book: warren B. Powell Approximate Dynamic Programming has some more in)
        if np.random.uniform() < explore_prob:
            # Explore Randomly
            operator_number = self.llh_dict[rd.choices(self.llh_names[:-1])[0]]
        else:
            # Exploit best action
            operator_number = self.agent.getBestAction()
        
        # Set a dummy new state to get into the while loop
        self.agent.setNewState((1,None))

        # How many times operator has been taken
        self.NVisits[self.agent.getCurrentState()+(operator_number,)] += 1

        # Find dynamic learning rate
        self.agent.setLearnRate(1/self.NVisits[self.agent.getCurrentState()+(operator_number,)])

        # Hold current score to evaluate reward later on
        current_score = self.solution_check(solution)["Cost"]

        # Applying the sequence
        while self.llh_names[operator_number] != "End" and self.agent.getNewState()[0] < self.max_sequence_length: 
            # Apply operator
            new_solution = eval("llh."+self.llh_names[operator_number]+"(self.data,solution)")

            # Add the operator used to the new_solution
            new_solution["operator"] = self.llh_names[operator_number]

            #New state is now length of the sequence and last LLH chosen
            self.agent.setNewState((self.agent.getCurrentState()[0] + 1, operator_number))

            #evaluate new solution score
            new_score = self.solution_check(new_solution)["Cost"]
            
            #evaluate reward = move in score for qlearner
            your_mums_reward = min(max(current_score - new_score,0),1)

            #Q-learning update
            self.agent.QLearningUpdate(action = operator_number, reward = your_mums_reward)

            #New state now becomes the current state
            self.agent.setCurrentState(self.agent.getNewState())

            current_score = new_score

            self.episode += 1

            explore_prob = self.min_explore + (self.max_explore - self.min_explore)*np.exp(-self.explore_decay_rate*self.episode)

            #apply the epsilon-greedy policy again
            if np.random.uniform() < explore_prob:
                #Explore Randomly
                # Note!! this time we can choose 0 to exit out of the LLH sequence
                operator_number = self.llh_dict[rd.choices(self.llh_names)[0]]
                #update new state with sequence length+1 and next used operator
                self.agent.setNewState((self.agent.getCurrentState()[0] + 1,operator_number))
            else:
                #Exploit best action
                operator_number = self.agent.getBestAction()
                 #update new state with sequence length+1 and next used operator
                self.agent.setNewState((self.agent.getCurrentState()[0] + 1,operator_number))

            self.NVisits[self.agent.getCurrentState()+(operator_number,)] += 1

            #find dynamic learning rate
            self.agent.setLearnRate(1/self.NVisits[self.agent.getCurrentState()+(operator_number,)])

        # Return final solution
        return new_solution