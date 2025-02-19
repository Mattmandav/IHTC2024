"""
This module contains all of the low level heuristic moves.
"""

import random as rd
import src.optimise.greedy as grd

"""
Function to ensure the "room_allocation", "theater_allocation" and "surgeon_allocation" are correct.
"""

# Update all allocations
def __update_allocations__(data,solution):
    # Initialising
    for d in data.all_days:
        # Room allocations
        for r in data.data["rooms"]:
            solution["room_allocation"][str((d,r["id"]))] = []
        # Theater allocations
        for t in data.data["operating_theaters"]:
            solution["theater_allocation"][str((d,t["id"]))] = t["availability"][d]
        # Surgeon allocations
        for s in data.data["surgeons"]:
            solution["surgeon_allocation"][str((d,s["id"]))] = s["max_surgery_time"][d]
    
    # Adding existing occupants
    for o in data.data["occupants"]:
        for i in range(o["length_of_stay"]):
            solution["room_allocation"][str((i,o["room_id"]))].append((o["id"],o["gender"],o["age_group"]))
    
    # Adding patients
    for p in solution["patients"]:
        patient_information = data.patient_dict[p["id"]]
        i0 = p["admission_day"]
        # Update room allocation
        for i in range(patient_information["length_of_stay"]):
            solution["room_allocation"][str((i0+i,p["room_id"]))].append((p["id"],
                                                                          patient_information["gender"],
                                                                          patient_information["age_group"])
                                                                          )
        # Update theater allocations
        solution["theater_allocation"][str((i0,t["id"]))] -= patient_information["surgery_duration"]
        # Update surgeon allocations
        solution["surgeon_allocation"][str((i0,patient_information["surgeon_id"]))] -= patient_information["surgery_duration"]
    
    # Return solution
    return solution


"""
Low-level moves
"""


# Insert a non-mandatory patient
def insert_patient(data,solution):
    """
    This operator takes a solution and tries to insert a single non-mandatory patient
    """
    # Creating a list of unassigned patients
    non_assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] == "none"]

    # If cannot remove patient then return
    if(len(non_assigned_patients) == 0):
        return solution
    
    # Selecting a patient to insert
    patient_to_insert = rd.choices(non_assigned_patients)[0]
    patient_information = data.patient_dict[patient_to_insert]

    # Selecting random features for solution
    new_solution_entry = {"id": patient_to_insert,
                            "admission_day": rd.choices(patient_information["possible_admission_days"])[0],
                            "room": rd.choices(patient_information["possible_rooms"])[0],
                            "operating_theater": rd.choices(patient_information["possible_theaters"])[0]}
    
    # Creating new solution
    new_patients = []
    for current_patient in solution["patients"]:
        if(current_patient["id"] != patient_to_insert):
            new_patients.append(current_patient)
        else:
            new_patients.append(new_solution_entry)
    solution["patients"] = new_patients

    # Return updated solution
    return solution

    
# Insert a non-mandatory patient to an empty room
def insert_patient_empty_room(data,solution):
    """
    This operator takes a solution and tries to insert a single non-mandatory patient into an entry room
    """
    # Creating a list of unassigned patients
    non_assigned_patients = [[patient["id"],sum(data.patient_dict[patient["id"]]["workload_produced"])] for patient in solution["patients"] if patient["admission_day"] == "none"]

    # If cannot remove patient then return
    if(len(non_assigned_patients) == 0):
        return solution

    # Selecting a patient to insert - least workload
    patient_to_insert = min(non_assigned_patients, key=lambda x: x[1])[0]

    # Find a day/room/theatre that works for this patient
    looking = True
    d=0
    while looking and d<data.ndays:
        # try allocating
        [solution,admitted,patient_admission] = grd.greedy_patient_allocation(data,solution,d,patient_to_insert)
        if(admitted):
            # Creating new solution
            new_patients = []
            for current_patient in solution["patients"]:
                if(current_patient["id"] != patient_to_insert):
                    new_patients.append(current_patient)
                else:
                    new_patients.append(patient_admission)
            solution["patients"] = new_patients
            looking = False
        else:
            d+=1

    # Return updated solution
    return solution


# Remove a non-mandatory patient
def remove_patient(data,solution):
    """
    This operator takes a solution and removes a single non-mandatory patient
    """
    # Creating a list of non-mandatory patients
    assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
    assigned_non_mandatory_patients = list(set(data.all_non_mandatory_patients) & set(assigned_patients))

    # If cannot remove patient then return
    if(len(assigned_non_mandatory_patients) == 0):
        return solution

    # Selecting a patient to remove
    patient_to_remove = rd.choices(assigned_non_mandatory_patients)[0]

    # Removing patient
    new_patients = []
    for current_patient in solution["patients"]:
        if(current_patient["id"] != patient_to_remove):
            new_patients.append(current_patient)
    solution["patients"] = new_patients

    # Return modified solution
    return solution


# Remove any patient
def remove_patient_any(data,solution):
    """
    This operator takes a solution and removes a single non-mandatory patient
    """
    # Creating a list of non-mandatory patients
    assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]

    # If cannot remove patient then return
    if(len(assigned_patients) == 0):
        return solution

    # Selecting a patient to remove
    patient_to_remove = rd.choices(assigned_patients)[0]

    # Removing patient
    new_patients = []
    for current_patient in solution["patients"]:
        if(current_patient["id"] != patient_to_remove):
            new_patients.append(current_patient)
    solution["patients"] = new_patients

    # Return modified solution
    return solution



# Applies the two moves sequentially
def remove_then_insert_patient(data,solution):
    solution = remove_patient(data,solution)
    solution = insert_patient(data,solution)
    return solution


# Applies the two moves sequentially
def remove_then_insert_patient_any(data,solution):
    solution = remove_patient_any(data,solution)
    solution = insert_patient(data,solution)
    return solution


# Changes room for a patient
def change_patient_room(data,solution):
    # Get all of the assigned patients
    assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
    if(len(assigned_patients) == 0):
        return solution

    # Selecting a patient to move
    patient_to_move = rd.choices(assigned_patients)[0]

    # Iterate through patients until find entry
    for p in solution["patients"]:
        if(p["id"] == patient_to_move):
            patient_rooms = data.patient_dict[patient_to_move]["possible_rooms"]
            current_room = p["room"]
            room_options = list(set(patient_rooms) - set([current_room]))
            if(len(room_options) != 0):
                new_room = rd.choices(room_options)[0]
                p["room"] = new_room
            break
    
    # Return modifed solution
    return solution


def change_patient_admission(data,solution):
    # Get all of the assigned patients
    assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
    if(len(assigned_patients) == 0):
        return solution

    # Selecting a patient to move
    patient_to_move = rd.choices(assigned_patients)[0]

    # Iterate through patients until find entry
    for p in solution["patients"]:
        if(p["id"] == patient_to_move):
            patient_days = data.patient_dict[patient_to_move]["possible_admission_days"]
            current_day= p["admission_day"]
            day_options = list(set(patient_days) - set([current_day]))
            if(len(day_options) != 0):
                new_day = rd.choices(day_options)[0]
                p["admission_day"] = new_day
            break
    
    # Return modifed solution
    return solution


def change_patient_theater(data,solution):
    # Get all of the assigned patients
    assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
    if(len(assigned_patients) == 0):
        return solution

    # Selecting a patient to move
    patient_to_move = rd.choices(assigned_patients)[0]

    # Iterate through patients until find entry
    for p in solution["patients"]:
        if(p["id"] == patient_to_move):
            patient_theaters = data.patient_dict[patient_to_move]["possible_theaters"]
            current_theater = p["operating_theater"]
            theater_options = list(set(patient_theaters) - set([current_theater]))
            if(len(theater_options) != 0):
                new_theater = rd.choices(theater_options)[0]
                p["operating_theater"] = new_theater
            break
    
    # Return modifed solution
    return solution


def add_nurse_room(data,solution):
    # Calling from a list of all nurses and selecting one
    nurse_id = rd.choices(data.all_nurses)[0]
    nurse = data.nurse_dict[nurse_id]

    # Selecting a shift and a room to add
    all_rooms = [room["id"] for room in data.data["rooms"]]
    shift = rd.choices(nurse["working_shifts"])[0]
    room = rd.choices(all_rooms)[0]

    # Updating the working shifts
    new_nurse_assignments = []
    for nurse_sol in solution["nurses"]:
        if(nurse_sol["id"] == nurse_id):
            updated_solution = False
            # Try and modify existing assignment
            for assignment in nurse_sol["assignments"]:
                if(assignment["day"] == shift["day"] and
                    assignment["shift"] == shift["shift"]):
                    assignment["rooms"].append(room)
                    assignment["rooms"] = list(set(assignment["rooms"]))
                    updated_solution = True
            # If not modifying existing, add new
            if not updated_solution:
                new_assignment = {"day": shift["day"],
                                    "shift": shift["shift"],
                                    "rooms": [room]}
                nurse_sol["assignments"].append(new_assignment)
            new_nurse_assignments.append(nurse_sol)
        else:
            new_nurse_assignments.append(nurse_sol)

    # Updating the solution
    solution["nurses"] = new_nurse_assignments

    # Return modified solution
    return solution


def remove_nurse_room(data,solution):
    # Calling from a list of all nurses and selecting one
    nurse_id = rd.choices(data.all_nurses)[0]

    # Updating the working shifts
    new_nurse_assignments = []
    for nurse_sol in solution["nurses"]:
        # Check if nurse selected is chosen
        if(nurse_sol["id"] == nurse_id):
            # Checking nurse has assignments
            if(len(nurse_sol["assignments"]) == 0):
                new_nurse_assignments.append(nurse_sol)
            else:
                # Choose an assignment
                assignment_index = rd.choices(list(range(len(nurse_sol["assignments"]))))[0]
                new_assignment = nurse_sol["assignments"][assignment_index]
                # Check a room is assigned
                if(len(new_assignment["rooms"]) == 0):
                    new_nurse_assignments.append(nurse_sol)
                else:
                    # Modify rooms
                    new_assignment["rooms"] = rd.sample(new_assignment["rooms"],
                                                        k = len(new_assignment["rooms"])-1)
                    # Modify solution
                    nurse_sol["assignments"][assignment_index] = new_assignment
                    new_nurse_assignments.append(nurse_sol)
        else:
            new_nurse_assignments.append(nurse_sol)

    # Updating the solution
    solution["nurses"] = new_nurse_assignments
    
    # Return modified solution
    return solution