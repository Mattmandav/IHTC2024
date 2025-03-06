# Operation STOR-i Time(tabling): Our entry to IHTC-2024

## Authors
- Matthew Davison
- Graham Burgess
- Rebecca Hamm
- Ben Lowery
- Adam Page

## Abstract
Our open-source solution finding approach for the IHTC-2024 is composed of two phases. The first phase attempts to generate feasible solutions using a greedy heuristic. Mandatory patients are placed into a list and sequentially inserted into the schedule. If there are mandatory patients remaining, these patients are placed at the top of the list for the next pass. The schedule is emptied and this process repeats until all patients are admitted or the algorithm times out. Nurses are then sequentially placed onto shifts to satisfy the resulting workload.

Once an initial solution is found, the second phase uses a parallelised heuristic to improve this solution using a variety of moves. The size of the pool of solutions to be modified at each iteration is specified by the user and this work is spread over all available computing cores. Chains of moves are chosen according to one of three schemes: simple random, Monte-Carlo, or Q-learning. The acceptance of solutions is done according to one of two schemes: record-to-record or simulated annealing.

We tested various combinations of these schemes to learn what would produce the best solutions for submission to the competition. This led to some interesting observations and outcomes.
