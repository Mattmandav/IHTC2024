import os
import subprocess

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
data_folder = "data"
solutions_folder = "solutions"
time_taken = 600
time_tolerance = 5

# Bulk running
data = sorted(os.listdir(data_folder))
for d in data:
    print(f"Optimising instance {d}")
    subprocess.run(
            ['python', 'main.py', '{}/{}'.format(data_folder,d), 
             '--output_folder', '{}'.format(solutions_folder),
             '--time_limit', '{}'.format(time_taken),
             '--time_tolerance', '{}'.format(time_tolerance)]
            )
