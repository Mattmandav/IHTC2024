import json
import subprocess
import os
import time
import multiprocessing as mp
import copy
import numpy as np
import random as rd
from src import QLearner #not sure why this has a squigly line


# Main optimisation function
def main(input_file, seed = 982032024, time_limit = 60, time_tolerance = 5):
    # Starting function timer
    time_start = time.time()

    # Open and read the JSON file
    with open(input_file, 'r') as file:
        data = json.load(file)

    # Set seed for optimisation
    rd.seed(seed)

    # Check if temp folder exists, make it if not
    if not os.path.exists("src/temp_solutions"):
        os.makedirs("src/temp_solutions")# Check if temp folder exists, make it if not

    # Put the data into the optimiser class
    optimisation_object = Optimiser(data,
                                    time_limit = time_limit,
                                    time_tolerance = time_tolerance)

    # Run an optimisation method
    solution = optimisation_object.optimise(method = "greedy")
    solution = optimisation_object.improvement_hyper_heuristic(solution)
    print(optimisation_object.solution_check(solution))

    # Remove the temporary solutions folder
    if os.path.exists("src/temp_solutions"):
        os.rmdir("src/temp_solutions")

    # Reporting process
    print(f"Main function completed in {round(time.time() - time_start,2)} seconds!")
    print()

    return solution


# Optimisation class
class Optimiser():
    def __init__(self, data, time_limit = 60, time_tolerance = 5):
        # Key values for optimiser
        self.data = data
        self.cores = 4
        self.remaining_time = time_limit
        self.time_start = time.time()
        self.time_tolerance = time_tolerance

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


        max_sequence_length = 10 # putting one here to allow for test case to be ran
        number_of_low_level_heuristics = 8 # putting one here to allow for test case to be ran
        base_learn_rate = 0.1
        discount_factor = 1
        #need self object for the qlearner agent, so this is can be called later on
        self.agent = QLearner.QLearner(
            n_states = (max_sequence_length,number_of_low_level_heuristics+2), #need pointers for these 2 values
            n_actions = number_of_low_level_heuristics + 2, #Plus one to signfy the action of ending the sequence of LLHs
            learn_rate = base_learn_rate,
            discount_factor = discount_factor,
            q_table = None,
            current_state = None,
            new_state = None     
        )

        #Initialise the qtable using inputs above
        #Default q_value is 0.0, set to 1.0 to be optimistic (if using 1-0 reward)
        starting_q_value = 1.0
        self.agent.initialiseQTable(q_value = starting_q_value)

        self.remaining_time = self.remaining_time - (time.time() - self.time_start)
    

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

    def solution_check(self, solution, core_name = ""):
        # Export data
        with open("src/temp_solutions/data{}.json".format(core_name), "w") as outfile: 
            json.dump(self.data, outfile, indent=2)
        # Export solution
        with open("src/temp_solutions/solution{}.json".format(core_name), "w") as outfile: 
            json.dump(solution, outfile, indent=2)
        
        # Check solution
        violations = 0
        cost = 0
        reasons = []
        result = subprocess.run(
            ['./IHTP_Validator', 'src/temp_solutions/data{}.json'.format(core_name), 'src/temp_solutions/solution{}.json'.format(core_name)],
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
        os.remove("src/temp_solutions/data{}.json".format(core_name))
        os.remove("src/temp_solutions/solution{}.json".format(core_name))
        
        # Return violations and cost
        return {"Violations": violations, "Cost": cost, "Reasons": reasons}


    def solution_score(self, solution, core_name):
        values = self.solution_check(solution, core_name=core_name)
        if(values["Violations"] > 0):
            return float('inf')
        else:
            return values["Cost"]


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
            # Timing iteration of patient assignment
            time_start = time.time()

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

            # Record time taken
            self.remaining_time = self.remaining_time - (time.time() - time_start)

            # Loop again if not all patients are allocated
            if(len(not_allocated) == 0):
                break
            # If not enough time return current solution
            elif(self.remaining_time <= self.time_tolerance):
                print("Exiting greedy algo due to time limit")
                return solution
            else:
                all_mandatory_patients = not_allocated + admitted_mandatory_patients

        # Timing nurse addition and non-mandatory patients
        time_start = time.time()

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

        # Recording time
        self.remaining_time = self.remaining_time - (time.time() - time_start)

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
    

    """
    Hyper-heurisic improvement
    """
    
    def improvement_hyper_heuristic(self, solution, pool_size = 4):
        """
        The improvement heuristic applies 4 moves at the same time to the current solution.
        It will never accept an infeasible solution.
        If we have multiple feasible the "best" solution has a chance of being selected as current.
        100% chance if solution is improving or equivalent.
        p% chance if the solution is not improving.
        The best solution is always saved.
        """
        # Checking if we have time to improve solution
        if(self.remaining_time <= self.time_tolerance):
            return solution
        
        # Preallocating features
        print(f"Starting hyper-heuristic (Remaining time: {round(self.remaining_time,2)} seconds)")
        best_solution = solution
        best_solution_value = self.solution_check(solution)["Cost"]
        current_solution = solution
        current_solution_value = self.solution_check(solution)["Cost"]
        
        # Applying heuristic
        while self.remaining_time > self.time_tolerance:
            # Timing iteration
            time_start = time.time()

            # Making copies of solution
            solution_pool = []
            for p in range(pool_size):
                solution_pool.append(copy.deepcopy(current_solution))

            # Applying moves
            index_sols = [(solution_pool[p],p) for p in range(pool_size)]
            with mp.Pool(self.cores) as p:
                new_solutions = p.starmap(self.solution_adjustment,index_sols)
            #with mp.Pool(self.cores) as p:
                #new_solutions = p.map(self.solution_adjustment,solution_pool)      

            # Checking solution pool for "best" solution
            index_new_sols = [(new_solutions[p],p) for p in range(pool_size)]
            with mp.Pool(self.cores) as p:
                values = p.starmap(self.solution_score,index_new_sols)

            # Selecting best solution of this pool
            temp_best = copy.deepcopy(new_solutions[np.argmin(values)])
            temp_best_value = self.solution_check(temp_best)["Cost"]
            temp_best_violations = self.solution_check(temp_best)["Violations"]

            # Checking that the best solution is feasible
            if(temp_best_violations > 0):
                continue

            # Saving best solution
            if(temp_best_value < best_solution_value):             
                print("New best solution found! Score:",temp_best_value)
                best_solution = copy.deepcopy(temp_best)
                best_solution_value = copy.deepcopy(temp_best_value)

            # Deciding whether to accept new solution as current solution
            if(temp_best_value < current_solution_value):
                current_solution = copy.deepcopy(temp_best)
                current_solution_value = copy.deepcopy(temp_best_value)

            # Updating the time remaining
            self.remaining_time = self.remaining_time - (time.time() - time_start)

        # Return the best solution
        return best_solution

    
    def solution_adjustment(self,solution,runnumber):
        """
        POSSIBLE PATIENT MOVES
        - Remove non-mandatory patient
        - Insert non-mandatory patient
        - Change room of patient
        - Change admission day
        - Change operating theater
        - Swap two patients between rooms
        - Swap two patients admission days
        - Swap two patients operating theater

        POSSIBLE NURSE MOVES
        - Add a room assignment
        - Remove a room assignment
        - Swap a room assignment
        - Add a shift
        - Remove a shift
        """
        new_solution = solution
        number_of_low_level_heuristics = 8
        max_sequence_length = 10
        self.agent.setCurrentState((0, number_of_low_level_heuristics + 1))
        # Select an operator to use
        # operator =  rd.choices([1,2,3,4,5,6,7,8])[0]

        #epsilon-Greedy policy for picking actions dervied from Q
        #Magic number here - can be changed and switched to a better regime
        explore_prob = 0.1
        #e.g. decaying epslion-greedy, UCB (Book: warren B. Powell Approximate Dynamic Programming has some more in)
        if np.random.uniform() < explore_prob:
            #Explore Randomly
            operator =  rd.choices([1,2,3,4,5,6,7,8])[0]
        else:
            #Exploit best action
            operator = self.agent.getBestAction()
        
        #set a dummy new state to get into the while loop
        self.agent.setNewState((1,None))

        #hold current score to evaluate reward later on
        current_score = self.solution_check(solution,runnumber)["Cost"]

        while operator != 0 and self.agent.getNewState()[0] < max_sequence_length: 

            # Operator 1: Insert an unassigned patient
            if(operator == 1):
                new_solution = self.insert_patient(solution)

            # Operator 2: Remove an assigned patient
            if(operator == 2):
                new_solution = self.remove_patient(solution)

            # Operator 3: Remove then insert (1+2)
            if(operator == 3):
                new_solution = self.remove_patient(solution)
                new_solution = self.insert_patient(new_solution)

            # Operator 4: Add a room for nurse
            if(operator == 4):
                new_solution = self.add_nurse_room(solution)

            # Operator 5: Remove a room for nurse
            if(operator == 5):
                new_solution = self.remove_nurse_room(solution)

            # Operator 6: Change a patients room
            if(operator == 6):
                new_solution = self.change_patient_room(solution)
            
            # Operator 7: Change a patients admission day
            if(operator == 7):
                new_solution = self.change_patient_admission(solution)

            # OPerator 8: Change a patients 
            if(operator == 8):
                new_solution = self.change_patient_theater(solution)
            
            #New state is now length of the sequence and last LLH chosen
            self.agent.setNewState((self.agent.getCurrentState()[0] + 1,operator))

            #evaluate new solution score
            new_score = self.solution_check(new_solution,runnumber)["Cost"]
            
            #evaluate reward = move in score for qlearner
            your_mums_reward = current_score - new_score

            #Q-learning update
            self.agent.QLearningUpdate(action = operator, reward = your_mums_reward)

            #New state now becomes the current state
            self.agent.setCurrentState(self.agent.getNewState())

            current_score = new_score
            #apply the epsilon-greedy policy again
            if np.random.uniform() < explore_prob:
                #Explore Randomly
                # NOTE!! this time we can choose 0 to exit out of the LLH sequence
                operator =  rd.choices([0,1,2,3,4,5,6,7,8])[0]
                #update new state with sequence length+1 and next used operator
                self.agent.setNewState((self.agent.getCurrentState()[0] + 1,operator))
            else:
                #Exploit best action
                operator = self.agent.getBestAction()
                 #update new state with sequence length+1 and next used operator
                self.agent.setNewState((self.agent.getCurrentState()[0] + 1,operator))

        # Return final solution
        return new_solution
    
    """
    Q-Learning for the heuristic sequence selection within the Hyper-Heuristic
    """

    
    """
    Individual adjustments to the solution
    """

    # Insert a non-mandatory patient
    def insert_patient(self,solution):
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
        patient_information = self.patient_dict[patient_to_insert]

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


    def remove_patient(self,solution):
        """
        This operator takes a solution and removes a single non-mandatory patient
        """
        # Creating a list of non-mandatory patients
        all_non_mandatory_patients = [patient_id for patient_id in self.patient_dict if not self.patient_dict[patient_id]["mandatory"]]
        assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
        assigned_non_mandatory_patients = list(set(all_non_mandatory_patients) & set(assigned_patients))

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
    

    def change_patient_room(self,solution):
        # Get all of the assigned patients
        assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
        if(len(assigned_patients) == 0):
            return solution

        # Selecting a patient to move
        patient_to_move = rd.choices(assigned_patients)[0]

        # Iterate through patients until find entry
        for p in solution["patients"]:
            if(p["id"] == patient_to_move):
                patient_rooms = self.patient_dict[patient_to_move]["possible_rooms"]
                current_room = p["room"]
                room_options = list(set(patient_rooms) - set([current_room]))
                if(len(room_options) != 0):
                    new_room = rd.choices(room_options)[0]
                    p["room"] = new_room
                break
        
        # Return modifed solution
        return solution
    

    def change_patient_admission(self,solution):
        # Get all of the assigned patients
        assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
        if(len(assigned_patients) == 0):
            return solution

        # Selecting a patient to move
        patient_to_move = rd.choices(assigned_patients)[0]

        # Iterate through patients until find entry
        for p in solution["patients"]:
            if(p["id"] == patient_to_move):
                patient_days = self.patient_dict[patient_to_move]["possible_admission_days"]
                current_day= p["admission_day"]
                day_options = list(set(patient_days) - set([current_day]))
                if(len(day_options) != 0):
                    new_day = rd.choices(day_options)[0]
                    p["admission_day"] = new_day
                break
        
        # Return modifed solution
        return solution
    

    def change_patient_theater(self,solution):
        # Get all of the assigned patients
        assigned_patients = [patient["id"] for patient in solution["patients"] if patient["admission_day"] != "none"]
        if(len(assigned_patients) == 0):
            return solution

        # Selecting a patient to move
        patient_to_move = rd.choices(assigned_patients)[0]

        # Iterate through patients until find entry
        for p in solution["patients"]:
            if(p["id"] == patient_to_move):
                patient_theaters = self.patient_dict[patient_to_move]["possible_theaters"]
                current_theater = p["operating_theater"]
                theater_options = list(set(patient_theaters) - set([current_theater]))
                if(len(theater_options) != 0):
                    new_theater = rd.choices(theater_options)[0]
                    p["operating_theater"] = new_theater
                break
        
        # Return modifed solution
        return solution

    
    def add_nurse_room(self,solution):
        # Creating a list of all nurses and selecting one
        all_nurses = [nurse_id for nurse_id in self.nurse_dict]
        nurse_id = rd.choices(all_nurses)[0]
        nurse = self.nurse_dict[nurse_id]

        # Selecting a shift and a room to add
        all_rooms = [room["id"] for room in self.data["rooms"]]
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

    
    def remove_nurse_room(self,solution):
        # Creating a list of all nurses and selecting one
        all_nurses = [nurse_id for nurse_id in self.nurse_dict]
        nurse_id = rd.choices(all_nurses)[0]

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