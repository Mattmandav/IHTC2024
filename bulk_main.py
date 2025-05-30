import os
import subprocess
import argparse
import json

"""
Under competition settings:
- 30 instances + 10 test instances
- 4 cores
- 10 minutes wall-time maximum (600 seconds)
- Can vary pool size
- Can vary time tolerance to ensure in limit

Should take a maximum of 400 minutes (7 hours) to re-run all instances.
"""

# Parameters
data_folder = "data/instances"
solutions_folder = "data/solutions"
time_taken = 600
time_tolerance = 60

# Arguments
parser = argparse.ArgumentParser()
parser.add_argument('--check',action='store_true')
parser.add_argument('--run',action='store_true')
args = parser.parse_args()


# Bulk checking
def bulk_check():
    solutions = sorted([
        f for f in os.listdir(solutions_folder)
        if os.path.isfile(os.path.join(solutions_folder, f))
        ])
    print(solutions)
    for s in solutions:
        if("test_" in s):
            continue
        d = s[4:]
        data = '{}/{}'.format(data_folder,d)
        sol_file = '{}/{}'.format(solutions_folder,s)
        result = subprocess.run(
            ['./bin/IHTP_Validator', data, sol_file],
            capture_output = True, # Python >= 3.7 only
            text = True # Python >= 3.7 only
            )
        violations = 0
        cost = 0
        reasons = []
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
        print(f"INSTANCE {d}: Violations = {violations}, Cost = {cost}")


# Bulk running
def bulk_run():
    data = sorted(os.listdir(data_folder))
    for d in data:
        print(f"Optimising instance {d}")
        subprocess.run(
                ['python', 'main.py', 
                 str(d),
                 '--input_folder', data_folder, 
                 '--output_folder', solutions_folder,
                '--time_limit', '{}'.format(time_taken),
                '--time_tolerance', '{}'.format(time_tolerance),
                '--selection', 'none',
                '--acceptance', 'none',
                '--save_costs']
                )
        print()
    print()
    bulk_check()


# Doing things
if(args.run):
    bulk_run()
elif(args.check):
    bulk_check()
else:
    print("No argument selected!")
    print("--run   : Batch run instances.")
    print("--check : Batch check instances.")