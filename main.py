import argparse
import sys
import os
from src.optimise.optimiser import main
from src.utils.plotter import plot_objectives
import json
import pandas as pd

if __name__ == "__main__":
    # Checking if enough arguments are given
    if(len(sys.argv) <= 1):
        raise ValueError("Provide path to input file")
    else:
        # Collecting arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('input_file',type=str,)
        parser.add_argument('--seed',type=int,default=42)
        parser.add_argument('--input_folder',type=str,default="data/instances")
        parser.add_argument('--output_folder',type=str,default="data/solutions")
        parser.add_argument('--time_limit',type=float,default="600")
        parser.add_argument('--time_tolerance',type=float,default="5")
        parser.add_argument('--plot',action='store_true')
        parser.add_argument('--verbose',action='store_true')
        parser.add_argument('--selection',type=str,default="random",choices=["qlearner","random","mcrl","none"])
        parser.add_argument('--acceptance',type=str,default="sa",choices=["improve_only","r2r","sa","none"])
        parser.add_argument('--sequence_length',type=int,default=0)
        parser.add_argument('--save_costs',action='store_true')
        parser.add_argument('--costs_folder',type=str,default="data/individual_costs")
        args = parser.parse_args()

        # Set the sequence length to be 1 if we are using random and 10 for the Q-Learner if not set explicitly
        if args.sequence_length == 0:
            if args.selection == "random":
                args.sequence_length = 1
            elif args.selection == "qlearner":
                args.sequence_length = 4
            elif args.selection == "mcrl":
                args.sequence_length = 4
            elif args.selection == "none":
                args.sequence_length = 0

        # Extracting filename
        filename = args.input_file[:-5]

        # Constructing input path
        path = args.input_file
        if(len(args.input_folder) > 0):
            path = "{}/".format(args.input_folder) + str(args.input_file)
        if os.path.isfile(path):
            filename_and_path = path
        else:
            raise ValueError("Invalid input file/folder")

        # Constructing output path
        if(len(args.output_folder) > 0):
            if os.path.exists(args.output_folder):
                args.output_folder = "{}/".format(args.output_folder)
            else:
                raise ValueError("Invalid output folder")
            
        # Running optimisation
        solution, costs = main(filename_and_path,
                               seed = args.seed,
                               time_limit = args.time_limit,
                               time_tolerance = args.time_tolerance,
                               verbose = args.verbose,
                               heuristic_selection=args.selection,
                               sequence_length=args.sequence_length,
                               acceptance_selection=args.acceptance)

        # Saving solution
        with open("{}sol_{}.json".format(args.output_folder,filename), "w") as outfile: 
            #solution.pop('operator')
            json.dump(solution, outfile, indent=2)

        # Save costs
        if(args.save_costs):
            if(len(args.costs_folder) > 0):
                if os.path.exists(args.costs_folder):
                    costs_name = "{}_{}_{}.csv".format(args.input_file[:3], args.selection, args.acceptance)
                    costs_path = "{}/{}".format(args.costs_folder,costs_name)
                    costs_dataframe = pd.DataFrame.from_dict(costs)
                    costs_dataframe.to_csv(costs_path, index=False) 
                else:
                    raise ValueError("Invalid output folder")
        
        # plot costs over time
        if(args.plot):
            plot_objectives(costs = costs)
