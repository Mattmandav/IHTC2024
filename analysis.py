from optimise.optimiser import main
import pandas as pd
from plotnine import *

def analyse():
    data = []

    # Running optimisation
    for i in range(9):
        input_file = 'tests/test0' + str(i+1) + '.json'    
        solution, costs = main(input_file, time_limit = 60)
        data = data + costs
    data = pd.DataFrame(data, columns=['Test#','Sol#','CostsType','Costs'])
    return(data)
