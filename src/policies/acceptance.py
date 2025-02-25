import math
import time
import random
def simulated_annealing(solution_value,new_solution_value,start_time,time_limit):
    if new_solution_value <= solution_value:
        return True
    evaluation_time=time.time()-start_time
    try:
        p=math.exp((solution_value-new_solution_value)/(10000*(1-(evaluation_time/time_limit))))
        #print(solution_value-new_solution_value,p)
    except OverflowError:
        p=-float("inf")
    if random.random()<p:
        return True
    else:
        return False
def improve_and_equal(solution_value,new_solution_value):
    if new_solution_value <= solution_value:
        return True
    else:
        return False