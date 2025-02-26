import time

def greedy_allocation(data, time_limit = 60, time_tolerance = 5):
    """
    PATIENT ASSIGNMENT FIRST
    Iterate through days, then iterate through patients:
    - If mandatory and can be admitted on that day, we admit the patient. All non-essential patients are omitted for now.
    - Choice of room is the first with space obeying gender at that point in the decision making.
    - Choice of theater is the one with the most capacity at that point in the decision making.
    - Once a patient is admitted they become occupants and are fixed in place.
    - If patient cannot be admitted they are kept in the list until assigned (or we run out of days).

    NURSE ASSIGNMENT SECOND
    Iterate through days, then iterate through nurses:
    - We now know the workload of each day, which we will try to meet as closely as possible.

    The greedy algorithm will never break the following constraints:
    - RoomGenderMix
    - PatientRoomCompatibility
    - SurgeonOvertime
    - OperatingTheaterOvertime
    - AdmissionDay
    - RoomCapacity
    - NursePresence

    The greedy algorithm might not be able to satisfy:
    - MandatoryUnscheduledPatients
    - UncoveredRoom
    """
    # Creating and sorting a list of mandatory patients (earliest admission date then if same date patient with tighter dates)
    all_mandatory_patients = [(patient_id,data.patient_dict[patient_id]["possible_admission_days"][0],len(data.patient_dict[patient_id]["possible_admission_days"]))
                                for patient_id in data.patient_dict 
                                if data.patient_dict[patient_id]["mandatory"]]
    all_mandatory_patients = sorted(all_mandatory_patients, key=lambda x: (x[1],x[2]))
    all_mandatory_patients = [p[0] for p in all_mandatory_patients]
    
    # Timing iteration of patient assignment
    time_start = time.time()
    
    while True:
        # Preallocating solution
        solution = {"patients": [],
                    "nurses": [],
                    "room_allocation": {},
                    "theater_allocation": {},
                    "surgeon_allocation": {}}

        # Building room capacity tracking object
        for d in data.all_days:
            for r in data.data["rooms"]:
                solution["room_allocation"][str((d,r["id"]))] = []

        # Theater capacity tracking
        for d in data.all_days:
            for t in data.data["operating_theaters"]:
                solution["theater_allocation"][str((d,t["id"]))] = t["availability"][d]

        # Surgeon capacity tracking
        for d in data.all_days:
            for s in data.data["surgeons"]:
                solution["surgeon_allocation"][str((d,s["id"]))] = s["max_surgery_time"][d]

        # Adding in occupants
        for o in data.data["occupants"]:
            for i in range(o["length_of_stay"]):
                solution["room_allocation"][str((i,o["room_id"]))].append((o["id"],o["gender"],o["age_group"]))
        
        # Iterating over mandatory patients
        admitted_mandatory_patients = []
        for d in data.all_days:
            for patient_id in all_mandatory_patients:
                # Check if already admitted 
                if(patient_id in admitted_mandatory_patients):
                    continue
                # If not try allocating
                [solution,admitted,patient_admission] = greedy_patient_allocation(data,solution,d,patient_id)
                if(admitted):
                    solution["patients"].append(patient_admission)
                    admitted_mandatory_patients.append(patient_id)

        # Checking if any people are not allocated
        not_allocated = []
        for patient_id in all_mandatory_patients:
            if(patient_id not in admitted_mandatory_patients):
                not_allocated.append((patient_id,data.patient_dict[patient_id]["possible_admission_days"][0],len(data.patient_dict[patient_id]["possible_admission_days"])))
        not_allocated = sorted(not_allocated, key=lambda x: (x[1],x[2]))
        not_allocated = [p[0] for p in not_allocated]

        # Loop again if not all patients are allocated
        if(len(not_allocated) == 0):
            break
        if(time_limit-time_tolerance < time.time() - time_start):
            break
        else:
            all_mandatory_patients = not_allocated + admitted_mandatory_patients


    # Iterating over non-mandatory patients
    all_non_mandatory_patients = [patient_id for patient_id in data.patient_dict if not data.patient_dict[patient_id]["mandatory"]]
    for patient_id in all_non_mandatory_patients:
        solution["patients"].append({"id": patient_id, "admission_day": "none"})
    
    # Working out the workload for each (day,shift,room)
    workload_day_shift_room = {}
    for d in data.all_days:
        for r in data.data["rooms"]:
            occupants = [o[0] for o in solution["room_allocation"][str((d,r["id"]))]]
            for shift in data.shift_types:
                total_workload = 0
                for patient_id in occupants:
                    # Occupant from day zero
                    if("a" in patient_id):
                        for o in data.data["occupants"]:
                            if(patient_id == o["id"]):
                                total_workload += o["workload_produced"][data.shift_index_dict[(d,shift)]]
                                break
                    # New patient
                    else:
                        for p in solution["patients"]:
                            if(patient_id == p["id"]):
                                admission_day = p["admission_day"]
                                total_workload += data.patient_dict[patient_id]["workload_produced"][data.shift_index_dict[(d-admission_day,shift)]]
                                break
                workload_day_shift_room[(d,shift,r["id"])] = total_workload
    
    # Preparing the nurse allocations
    nurse_allocation = {}
    for nurse_id in data.nurse_dict:
        nurse_allocation[nurse_id] = {"id": nurse_id, "assignments": []}

    # Iterating over days, shifts, rooms and nurses to assign nurses
    for d in data.all_days:
        for shift in data.shift_types:
            # Ensuring at most one nurse per room
            rooms_with_nurse = []
            # Iterating over nurses
            for nurse_id in data.nurse_dict:
                # Check if a nurse can actually do this shift
                cannot_do_shift = True
                remaining_load = 0
                for working_shift in data.nurse_dict[nurse_id]["working_shifts"]:
                    if(working_shift["day"] == d and working_shift["shift"] == shift):
                        remaining_load = working_shift["max_load"]
                        cannot_do_shift = False
                if(cannot_do_shift):
                    continue
                # Working shift so assign workload
                rooms_assigned_to_nurse = []
                for r in data.data["rooms"]:
                    if(r["id"] in rooms_with_nurse):
                        continue
                    #elif(remaining_load >= workload_day_shift_room[(d,shift,r["id"])]):
                    elif(remaining_load >= 0):
                        rooms_assigned_to_nurse.append(r["id"])
                        rooms_with_nurse.append(r["id"])
                        remaining_load -= workload_day_shift_room[(d,shift,r["id"])]
                # Update the assignments
                if(len(rooms_assigned_to_nurse) > 0):
                    nurse_allocation[nurse_id]["assignments"].append({"day": d, 
                                                                        "shift": shift, 
                                                                        "rooms": rooms_assigned_to_nurse})
    
    # Applying the nurses to the solution
    for nurse_id in data.nurse_dict:
        if(len(nurse_allocation[nurse_id]["assignments"]) > 0):
            solution["nurses"].append(nurse_allocation[nurse_id])

    return solution
    

def greedy_patient_allocation(data,solution,d,patient_id):
    original_solution = solution
    # Check if patient can be admitted on this day
    if(d in data.patient_dict[patient_id]["possible_admission_days"]):
        # Check if the surgeon has availability on that day
        surgeon_day_availability = solution["surgeon_allocation"][str((d,data.patient_dict[patient_id]["surgeon_id"]))]
        if(surgeon_day_availability >= data.patient_dict[patient_id]["surgery_duration"]):
            for r in data.data["rooms"]:
                room_day_info = solution["room_allocation"][str((d,r["id"]))]
                # Check if patient can fit into room
                if(len(room_day_info) < r["capacity"] and r["id"] in data.patient_dict[patient_id]["possible_rooms"]):
                    # Check if anyone is in room or check if patient matches gender of room
                    if(len(room_day_info) == 0 or room_day_info[0][1] == data.patient_dict[patient_id]["gender"]):
                        for t in data.data["operating_theaters"]:
                            # Checking if the theater has enough capacity to perform surgery
                            if(solution["theater_allocation"][str((d,t["id"]))] >= data.patient_dict[patient_id]["surgery_duration"]):
                                # ADMIT PATIENT
                                patient_admission = {"id": patient_id}
                                # Add day
                                patient_admission["admission_day"] = d
                                # Add room
                                patient_admission["room"] = r["id"]
                                for i in range(data.patient_dict[patient_id]["length_of_stay"]):
                                    if(d+i < data.ndays):
                                        solution["room_allocation"][str((d+i,r["id"]))].append((patient_id,
                                                                                data.patient_dict[patient_id]["gender"],
                                                                                data.patient_dict[patient_id]["age_group"]))
                                # Add theater
                                solution["theater_allocation"][str((d,t["id"]))] -= data.patient_dict[patient_id]["surgery_duration"]
                                patient_admission["operating_theater"] = t["id"]
                                # Update surgeons hours
                                solution["surgeon_allocation"][str((d,data.patient_dict[patient_id]["surgeon_id"]))] -= data.patient_dict[patient_id]["surgery_duration"]
                                # Return the admission details
                                return solution,True,patient_admission
    return original_solution,False,{}
