import json
import subprocess
import os
import time

# Main optimisation function
def main(input_file,seed):

    # Open and read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Put the data into the optimiser class
    optimisation_object = Optimiser(data)

    # Run an optimisation method
    solution = optimisation_object.optimise(method = "greedy")
    print(optimisation_object.solution_check(solution))

    return solution


# Optimisation class
class Optimiser():
    def __init__(self,data):
        # Saving the extracted JSON
        self.data = data

        # Extracting key information
        self.ndays = data["days"]
        self.all_days = [d for d in range(self.ndays)]
        self.skill_levels = data["skill_levels"]
        self.shift_types = data["shift_types"]

        # Day,Shift pair to Index
        self.shift_index_dict = {}
        for d in self.all_days:
            for shift in self.shift_types:
                self.shift_index_dict[(d,shift)] = len(self.shift_index_dict)
        
        # # Room information
        # self.room_capacity_dict = {}
        # for room in data["rooms"]:
        #     self.room_capacity_dict[room["id"]] = room["capacity"]

        # # Theater information
        # self.theater_capacity_dict = {}
        # for theater in data["operating_theaters"]:
        #     self.theater_capacity_dict[theater["id"]] = theater["availability"]

        # Patient information
        self.patient_dict = {}
        for patient in data["patients"]:
            self.patient_dict[patient["id"]] = {
                "mandatory": self.patient_mandatory(patient),
                "gender": patient["gender"],
                "age_group": patient["age_group"],
                "length_of_stay": patient["length_of_stay"],
                "workload_produced": patient["workload_produced"],
                "skill_level_required": patient["skill_level_required"],
                "surgeon_id": patient["surgeon_id"],
                "surgery_duration": patient["surgery_duration"],
                "possible_rooms": self.patient_possible_rooms(patient),
                "possible_theaters": self.patient_possible_theaters(patient),
                "possible_admission_days": self.patient_possible_admission_days(patient)
            }

        # Nurse information
        self.nurse_dict = {}
        for nurse in data["nurses"]:
            self.nurse_dict[nurse["id"]] = {
                "skill_level": nurse["skill_level"],
                "working_shifts": self.nurse_working_shifts(nurse)
            }
    

    """
    Processing functions
    """

    def patient_mandatory(self,patient):
        if(patient["mandatory"]):
            return True
        else:
            return False


    def patient_possible_rooms(self,patient):
        all_rooms = [r["id"] for r in self.data["rooms"]]
        room_list = list(set(all_rooms) - set(patient["incompatible_room_ids"]))
        return room_list
    

    def patient_possible_theaters(self,patient):
        theater_list = [t["id"] for t in self.data["operating_theaters"]]
        return theater_list


    def patient_possible_admission_days(self,patient):
        patient_days = [d for d in self.all_days if d >= patient["surgery_release_day"]]
        if(self.patient_mandatory(patient)):
            mandatory_patient_days = [d for d in patient_days if d <= patient["surgery_due_day"]]
            return mandatory_patient_days
        else:
            return patient_days
        
    
    def nurse_working_shifts(self,nurse):
        shift_list = []
        for shift in nurse["working_shifts"]:
            shift_list.append(shift)
        return shift_list


    """
    Solution checking
    """

    def solution_check(self, solution):
        # Export data
        with open("src/temp_solutions/data.json", "w") as outfile: 
            json.dump(self.data, outfile, indent=2)
        # Export solution
        with open("src/temp_solutions/solution.json", "w") as outfile: 
            json.dump(solution, outfile, indent=2)
        
        # Check solution
        violations = 0
        cost = 0
        reasons = []
        result = subprocess.run(
            ['.\IHTP_Validator', 'src/temp_solutions/data.json', 'src/temp_solutions/solution.json'],
            capture_output = True, # Python >= 3.7 only
            text = True # Python >= 3.7 only
            )
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
        
        # Clean up temp folder
        os.remove("src/temp_solutions/data.json")
        os.remove("src/temp_solutions/solution.json")
        
        # Return violations and cost
        return {"Violations": violations, "Cost": cost, "Reasons": reasons}


    """
    Optimisation functions
    """

    def optimise(self, method = None):
        if(method == None):
            print("Methods coming soon!")
            solution = {"patients": [], "nurses": []}
        elif(method == "greedy"):
            t0 = time.time()
            solution = self.greedy_allocation()
            print("Greedy approach took {} seconds".format(time.time()-t0))
        else:
            solution = {"patients": [], "nurses": []}
        # Returning the solution
        return solution


    def greedy_allocation(self):
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
        all_mandatory_patients = [(patient_id,self.patient_dict[patient_id]["possible_admission_days"][0],len(self.patient_dict[patient_id]["possible_admission_days"]))
                                   for patient_id in self.patient_dict 
                                   if self.patient_dict[patient_id]["mandatory"]]
        all_mandatory_patients = sorted(all_mandatory_patients, key=lambda x: (x[1],x[2]))
        all_mandatory_patients = [p[0] for p in all_mandatory_patients]
        
        while True:
            # Preallocating solution
            solution = {"patients": [], "nurses": []}

            # Building room capacity tracking object
            room_allocation = {}
            for d in self.all_days:
                for r in self.data["rooms"]:
                    room_allocation[(d,r["id"])] = []

            # Theater capacity tracking
            theater_allocation = {}
            for d in self.all_days:
                for t in self.data["operating_theaters"]:
                    theater_allocation[(d,t["id"])] = t["availability"][d]

            # Surgeon capacity tracking
            surgeon_allocation = {}
            for d in self.all_days:
                for s in self.data["surgeons"]:
                    surgeon_allocation[(d,s["id"])] = s["max_surgery_time"][d]

            # Adding in occupants
            for o in self.data["occupants"]:
                for i in range(o["length_of_stay"]):
                    room_allocation[(i,o["room_id"])].append((o["id"],o["gender"],o["age_group"]))
            
            # Iterating over mandatory patients
            admitted_mandatory_patients = []
            for d in self.all_days:
                for patient_id in all_mandatory_patients:
                    # Check if already admitted 
                    if(patient_id in admitted_mandatory_patients):
                        continue
                    # If not try allocating
                    [admitted,patient_admission,room_allocation,theater_allocation,surgeon_allocation] = self.greedy_patient_allocation(d,patient_id,room_allocation,theater_allocation,surgeon_allocation)
                    if(admitted):
                        solution["patients"].append(patient_admission)
                        admitted_mandatory_patients.append(patient_id)

            # Checking if any people are not allocated
            not_allocated = []
            for patient_id in all_mandatory_patients:
                if(patient_id not in admitted_mandatory_patients):
                    not_allocated.append((patient_id,self.patient_dict[patient_id]["possible_admission_days"][0],len(self.patient_dict[patient_id]["possible_admission_days"])))
            not_allocated = sorted(not_allocated, key=lambda x: (x[1],x[2]))
            not_allocated = [p[0] for p in not_allocated]

            # Loop again if not all patients are allocated
            if(len(not_allocated) == 0):
                break
            else:
                all_mandatory_patients = not_allocated + admitted_mandatory_patients

        # Iterating over non-mandatory patients
        all_non_mandatory_patients = [patient_id for patient_id in self.patient_dict if not self.patient_dict[patient_id]["mandatory"]]
        for patient_id in all_non_mandatory_patients:
            solution["patients"].append({"id": patient_id, "admission_day": "none"})
        
        # Working out the workload for each (day,shift,room)
        workload_day_shift_room = {}
        for d in self.all_days:
            for r in self.data["rooms"]:
                occupants = [o[0] for o in room_allocation[(d,r["id"])]]
                for shift in self.shift_types:
                    total_workload = 0
                    for patient_id in occupants:
                        # Occupant from day zero
                        if("a" in patient_id):
                            for o in self.data["occupants"]:
                                if(patient_id == o["id"]):
                                    total_workload += o["workload_produced"][self.shift_index_dict[(d,shift)]]
                                    break
                        # New patient
                        else:
                            for p in solution["patients"]:
                                if(patient_id == p["id"]):
                                    admission_day = p["admission_day"]
                                    total_workload += self.patient_dict[patient_id]["workload_produced"][self.shift_index_dict[(d-admission_day,shift)]]
                                    break
                    workload_day_shift_room[(d,shift,r["id"])] = total_workload
        
        # Preparing the nurse allocations
        nurse_allocation = {}
        for nurse_id in self.nurse_dict:
            nurse_allocation[nurse_id] = {"id": nurse_id, "assignments": []}

        # Iterating over days, shifts, rooms and nurses to assign nurses
        for d in self.all_days:
            for shift in self.shift_types:
                # Ensuring at most one nurse per room
                rooms_with_nurse = []
                # Iterating over nurses
                for nurse_id in self.nurse_dict:
                    # Check if a nurse can actually do this shift
                    cannot_do_shift = True
                    remaining_load = 0
                    for working_shift in self.nurse_dict[nurse_id]["working_shifts"]:
                        if(working_shift["day"] == d and working_shift["shift"] == shift):
                            remaining_load = working_shift["max_load"]
                            cannot_do_shift = False
                    if(cannot_do_shift):
                        continue
                    # Working shift so assign workload
                    rooms_assigned_to_nurse = []
                    for r in self.data["rooms"]:
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

        # # Checking for uncovered rooms
        # uncovered_rooms = []
        # for d in self.all_days:
        #     for shift in self.shift_types:
        #         for r in self.data["rooms"]:
        #             if(workload_day_shift_room[(d,shift,r["id"])] > 0):
        #                 room_covered = False
        #                 for nurse_id in nurse_allocation:
        #                     for assignment in nurse_allocation[nurse_id]["assignments"]:
        #                         if(assignment["day"] == d and 
        #                            assignment["shift"] == shift and 
        #                            r["id"] in assignment["rooms"]):
        #                             room_covered = True
        #                             break
        #                     if(room_covered):
        #                         break
        #                 if(not room_covered):
        #                     uncovered_rooms.append((d,shift,r["id"]))
        # print(uncovered_rooms)
        # print(len(uncovered_rooms))
        
        # Applying the nurses to the solution
        for nurse_id in self.nurse_dict:
            if(len(nurse_allocation[nurse_id]["assignments"]) > 0):
                solution["nurses"].append(nurse_allocation[nurse_id])

        return solution
    

    def greedy_patient_allocation(self,d,patient_id,room_allocation,theater_allocation,surgeon_allocation):
        # Check if patient can be admitted on this day
        if(d in self.patient_dict[patient_id]["possible_admission_days"]):
            # Check if the surgeon has availability on that day
            surgeon_day_availability = surgeon_allocation[(d,self.patient_dict[patient_id]["surgeon_id"])]
            if(surgeon_day_availability >= self.patient_dict[patient_id]["surgery_duration"]):
                for r in self.data["rooms"]:
                    room_day_info = room_allocation[(d,r["id"])]
                    # Check if patient can fit into room
                    if(len(room_day_info) < r["capacity"] and r["id"] in self.patient_dict[patient_id]["possible_rooms"]):
                        # Check if anyone is in room or check if patient matches gender of room
                        if(len(room_day_info) == 0 or room_day_info[0][1] == self.patient_dict[patient_id]["gender"]):
                            for t in self.data["operating_theaters"]:
                                # Checking if the theater has enough capacity to perform surgery
                                if(theater_allocation[(d,t["id"])] >= self.patient_dict[patient_id]["surgery_duration"]):
                                    # ADMIT PATIENT
                                    patient_admission = {"id": patient_id}
                                    # Add day
                                    patient_admission["admission_day"] = d
                                    # Add room
                                    patient_admission["room"] = r["id"]
                                    for i in range(self.patient_dict[patient_id]["length_of_stay"]):
                                        if(d+i < self.ndays):
                                            room_allocation[(d+i,r["id"])].append((patient_id,
                                                                                    self.patient_dict[patient_id]["gender"],
                                                                                    self.patient_dict[patient_id]["age_group"]))
                                    # Add theater
                                    theater_allocation[(d,t["id"])] -= self.patient_dict[patient_id]["surgery_duration"]
                                    patient_admission["operating_theater"] = t["id"]
                                    # Update surgeons hours
                                    surgeon_allocation[(d,self.patient_dict[patient_id]["surgeon_id"])] -= self.patient_dict[patient_id]["surgery_duration"]
                                    # Return the admission details
                                    return True,patient_admission,room_allocation,theater_allocation,surgeon_allocation
        return False,{},room_allocation,theater_allocation,surgeon_allocation