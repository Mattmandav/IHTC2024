import sys
import os
from src.optimise.optimiser import main
import json

instance_names = ['i' + '0' + str(num)+ '.json' if num < 10 else 'i' + str(num) + '.json' for num in range(1,31)]

if __name__ == "__main__":
    # Choice of instance as argument
    instance = instance_names[int(sys.argv[2])]
    # Configs to run
    params = {
        'random': {
            'sa': {'sequence_length': 1, 'delta_sa': 1000},
            #'r2r': {'sequence_length': 1, 'rho': 0.33},
            #'improve_only': {'sequence_length': 1}
        },
        'qlearner': {
            'sa': {'sequence_length': 2, 'delta_sa': 1, 'lambda_q': 0.002555141214583},
            #'r2r': {'sequence_length': 2, 'rho': 0.78, 'lambda_q': 0.03},
            #'improve_only': {'sequence_length': 2, 'lambda_q':  0.0011}
        },
        'mcrl': {
            'sa': {'sequence_length': 1, 'delta_sa': 100, 'lambda_q': 0.002392316742348},
            #'r2r': {'sequence_length': 2, 'rho': 0.005, 'lambda_q': 0.0036},
            #'improve_only': {'sequence_length': 2, 'lambda_q':  0.0022}
        },
    }
    # Run all combinations in params
    for selection in params:
        for acceptance in params[selection]:
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
            if acceptance == 'sa':
                delta_sa = params[selection][acceptance]['delta_sa']
            else:
                delta_sa = None
            solution, costs = main('data/instances/{}'.format(instance),
                                    seed = 42,
                                    time_limit = 7200, # 2 hour runs
                                    time_tolerance = 3,
                                    verbose = False,
                                    heuristic_selection=selection,
                                    acceptance_selection=acceptance,
                                    sequence_length=sequence_length,
                                    rho_r2r=rho,
                                    delta_sa=delta_sa,
                                    lambda_q=lambda_q,
                                    save_improvement_over_time=True
                                    )

            # Saving solution
            with open("{}/instance_{}_{}_sol_{}".format(sys.argv[1], selection, acceptance, instance), "w") as outfile: 
                #solution.pop('operator')
                json.dump(solution, outfile, indent=2)
