import argparse
import sys
import os
from src.optimise.optimiser import main
from src.utils.plotter import plot_objectives
import json

if __name__ == "__main__":
    # Checking if enough arguments are given
    if(len(sys.argv) <= 1):
        raise ValueError("Provide path to input file")
    else:
        # Collecting arguments
        parser = argparse.ArgumentParser()
        parser.add_argument('input_file',type=str,)
        parser.add_argument('--seed',type=int,default=982032024)
        parser.add_argument('--input_folder',type=str,default="data/instances")
        parser.add_argument('--output_folder',type=str,default="data/solutions")
        parser.add_argument('--time_limit',type=float,default="60")
        parser.add_argument('--time_tolerance',type=float,default="10")
        parser.add_argument('--plot',action='store_true')
        args = parser.parse_args()
        
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
                               time_tolerance = args.time_tolerance)

        # Saving solution
        with open("{}sol_{}.json".format(args.output_folder,filename), "w") as outfile: 
            json.dump(solution, outfile, indent=2)
        
        # plot costs over time
        if(args.plot):
            plot_objectives(costs = costs)
