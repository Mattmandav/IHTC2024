import sys
import os
from src.optimise.optimiser import main
import json

if __name__ == "__main__":
    params = {
        'random': {'r2r': {'sequence_length': 1, 'rho': 0.33}, 'improve_only': {'sequence_length': 1}},
        'qlearner': {'r2r': {'sequence_length': 2, 'rho': 0.78, 'lambda_q': 0.03}, 'improve_only': {'sequence_length': 2, 'lambda_q':  0.0011}},
        'mcrl': {'r2r': {'sequence_length': 2, 'rho': 0.005, 'lambda_q': 0.0036}, 'improve_only': {'sequence_length': 2, 'lambda_q':  0.0022}},
    }
    instance_names = ['m' + '0' + str(num)+ '.json' if num < 10 else 'm' + str(num) + '.json' for num in range(1,31)]
    for selection in ["random", "qlearner", 'mcrl']:
        for acceptance in ['r2r', 'improve_only']:
            for instance in instance_names:
                print('Selection: {}, acceptance: {}, instance: {}'.format(selection, acceptance, instance))
                # Running optimisation
                sequence_length = params[selection][acceptance]['sequence_length']
                if acceptance == 'r2r':
                    rho = params[selection][acceptance]['rho']
                else:
                    rho = None
                if selection == 'qlearner' or selection == 'mcrl':
                    lambda_q = params[selection][acceptance]['lambda_q']
                else:
                    lambda_q = None
                solution, costs = main('data/instances/{}'.format(instance),
                                        seed = 42,
                                        time_limit = 600,
                                        time_tolerance = 3,
                                        verbose = False,
                                        heuristic_selection=selection,
                                        acceptance_selection=acceptance,
                                        sequence_length=sequence_length,
                                        rho=rho,
                                        lambda_q=lambda_q
                                        )

                # Saving solution
                with open("{}/instance_{}_{}_sol_{}".format(sys.argv[1],selection, acceptance,instance), "w") as outfile: 
                    #solution.pop('operator')
                    json.dump(solution, outfile, indent=2)
