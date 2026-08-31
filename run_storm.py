import sys
import os
from src.optimise.optimiser import main
import json

if __name__ == "__main__":
    instance_names_comp = ['i' + '0' + str(num)+ '.json' if num < 10 else 'i' + str(num) + '.json' for num in range(1,31)]
    instance_names_final = ['m' + '0' + str(num)+ '.json' if num < 10 else 'i' + str(num) + '.json' for num in range(1,31)]
    instance_names = instance_names_comp + instance_names_final
    for instance in instance_names:
        # Running optimisation
        solution, costs = main('data/instances/{}'.format(instance),
                                seed = 42,
                                time_limit = 600,
                                time_tolerance = 5,
                                verbose = False,
                                heuristic_selection='random',
                                sequence_length=2)
        # Saving solution
        with open("{}/sol_{}".format(sys.argv[1],instance), "w") as outfile: 
            #solution.pop('operator')
            json.dump(solution, outfile, indent=2)
 