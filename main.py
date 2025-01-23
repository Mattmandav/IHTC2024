import argparse
import sys
import os
from src.optimiser import main
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
        parser.add_argument('--output_folder',type=str,default="")
        parser.add_argument('--time_limit',type=float,default="60")
        parser.add_argument('--time_tolerance',type=float,default="5")
        args = parser.parse_args()
        
        # Extracting filename
        index = args.input_file.rfind("/")
        if(index == -1):
            filename = args.input_file[:-5]
        else:
            filename = args.input_file[index+1:-5]

        # Constructing output path
        if(len(args.output_folder) > 0 ):
            if os.path.exists(args.output_folder):
                args.output_folder = "{}/".format(args.output_folder)
            else:
                raise ValueError("Invalid output folder")
            
        # Running optimisation
        solution = main(args.input_file,
                        seed = args.seed,
                        time_limit = args.time_limit,
                        time_tolerance = args.time_tolerance)

        # Saving solution
        with open("{}sol_{}.json".format(args.output_folder,filename), "w") as outfile: 
            json.dump(solution, outfile, indent=2)
