import math
import time
import random
def rr(values,new_solutions,temp_best_value,previous_values,pool_size):

    solution_pool = []
    new_values = []
    for i in range(len(values)):
        if(values[i]["Cost"] < previous_values[i]
            or values[i]["Cost"] < (temp_best_value + 0.01*temp_best_value)):
                solution_pool.append(new_solutions[i])
                new_values.append(values[i]["Cost"])
                """if self.verbose:
                    self.hits['successful'] += 1
                    self.hits['type'].append(temp_best['operator'])
                    self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)"""
                    
    return solution_pool , new_values
def bestrr(values,new_solutions,temp_best_value,previous_values,pool_size):

    solution_pool = []
    new_values = []
    for i in range(len(values)):
        if( values[i]["Cost"] < (temp_best_value + 0.01*temp_best_value)):
                solution_pool.append(new_solutions[i])
                new_values.append(values[i]["Cost"])
                """if self.verbose:
                    self.hits['successful'] += 1
                    self.hits['type'].append(temp_best['operator'])
                    self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)"""
                    
    return solution_pool , new_values
def simulated_annealing(values,new_solutions,previous_values,start_time,time_limit):
    solution_pool = []
    new_values = []
    for i in range(len(values)):
        if( values[i]["Cost"] < previous_values[i]):
                solution_pool.append(new_solutions[i])
                new_values.append(values[i]["Cost"])
                """if self.verbose:
                    self.hits['successful'] += 1
                    self.hits['type'].append(temp_best['operator'])
                    self.hits['Cost Reduction'].append(current_solution_value - temp_best_value)"""
                    
        else:
            evaluation_time=time.time()-start_time
            try:
                p=math.exp((previous_values[i]-values[i]["Cost"])/(1*(1-(evaluation_time/time_limit))))
            except OverflowError:
                p=-float("inf")
            if random.random()<p:
                solution_pool.append(new_solutions[i])
                new_values.append(values[i]["Cost"])
    return solution_pool , new_values