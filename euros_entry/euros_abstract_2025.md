# Operation STOR-i Time(tabling): Our entry to IHTC-2024

## Authors
- Matthew Davison
- Graham Burgess
- Rebecca Hamm
- Ben Lowery
- Adam Page

## Abstract
Nurse rostering is a highly complex optimisation problem where traditional exact methods become computationally infeasible for large instances. Our open-source meta-heuristic solution for the IHTC-2024 employs a two-phase strategy to construct and refine schedules.

In the first phase, we generate feasible solutions using a greedy heuristic. Mandatory patients are prioritised and sequentially inserted into the schedule. If any remain, they are re-prioritised for the next pass, and the schedule is reset. This process continues until all patients are admitted or the algorithm times out. Nurses are then assigned to shifts in sequence to meet workload demands. The second phase refines the initial solution using a parallelized heuristic, applying diverse sequences of moves to improve schedule quality. Moves are selected based on one of three strategies: Simple random, Monte-Carlo, or Q-learning. Solution acceptance follows either a record-to-record or simulated annealing scheme.

By experimenting with different methods, we gained insight into the best heuristic approaches for the IHTC-2024, leading to the results for competition submission. Our approach highlights the adaptability of heuristic methods and their capability for addressing complex rostering challenges.
