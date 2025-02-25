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
**H1 -** No gender mix: Patients of different genders may not share a room on any day.

**H2 -** Compatible rooms: Patients can only be assigned to one of their compatible rooms.

**H3 -** Surgeon overtime: The maximum daily surgery time of a surgeon must not be exceeded.

**H4 -** OT overtime: The duration of all surgeries allocated to an OT on a day must not exceed its maximum capacity.

**H5 -** Mandatory versus optional patients: All mandatory patients must be admitted within the scheduling period, whereas optional patients may be postponed to future scheduling periods.

**H6 -** Admission day: A patient can be admitted on any day from their release date to their due date. Given that optional patients do not have a due date, they can be admitted on any day after their release date.

**H7 -** Room capacity: The number of patients in each room in each day cannot exceed the capacity of the room.

**H8 -** Nurse presence: Nurses may only be assigned to shifts that they are working.

**H9 -** Uncovered room: If a room has a patient during a shift then there must be a nurse covering that room during that shift.
## Move Acceptance

