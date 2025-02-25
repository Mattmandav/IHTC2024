# IHTC2024 - TEAM NAME

This document contains the name of the team, the particpants of the team and a description of the method used.

## Team participants
All participants of team-name are PhD students at the STOR-i Centre for Doctoral Training based at Lancaster University, UK.

- Matthew Davison (contact: m.davison2@lancaster.ac.uk)
- Adam Page
- Ben Lowery
- Graham Burgess
- Rebecca Hamm

# Method 

## Overview
We first generate an initial Feasible Solution using a greedy heuristic. With the remaining clock time, we run an iterative hyper-heuristic procedure consisting of a move selection and move acceptance step. The move portion is parellelised, allowing for up to 4 different move evaluations for each iteration step. The algorithm is described more formally below. 

[INSERT LATEX ALGORITHM OR FLOWCHART?]

## Initial Feasible Solution

## Move Selection

### Low-level Heuristics
**Move 1 -** Insert non-mandatory patient

**Move 2 -** Insert a non-mandatory patient to an empty room

**Move 3 -** Insert a non-mandatory patient where a surgeon is available

**Move 4 -** Remove a single non-mandatory patient

**Move 5 -** Remove any patient

**Move 6 -** Remove then insert a non-mandatory patient sequentially 

**Move 7 -** Remove then insert any patient sequentially

**Move 8 -** Change a patient room

**Move 9 -** Change patient's admission day

**Move 10 -** Change a patient's theatre

**Move 11 -** Change a patient's room, admission, and theatre sequentially

**Move 12 -** Change a patient's room and admission sequentially

**Move 13 -** Change a patient's admission and theatre sequentially

**Move 14 -** Add a nurse to a room

**Move 15 -** Remove a nurse from a room
## Move Acceptance

