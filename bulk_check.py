import os
import subprocess

# Parameters
data_folder = "data"
solution_folder = "solutions"

# Bulk running
solutions = sorted(os.listdir(solution_folder))
for s in solutions:
    d = s[4:]
    result = subprocess.run(
        ['./IHTP_Validator', 
        '{}/{}'.format(data_folder,d), 
        '{}/{}'.format(solution_folder,s)],
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
    