"""
Class object to hold all of the instance data
"""

class Data():
    def __init__(self, raw_data):
        # Instance
        self.data = raw_data
        
        # Extracting key information
        self.ndays = raw_data["days"]
        self.all_days = [d for d in range(self.ndays)]
        self.skill_levels = raw_data["skill_levels"]
        self.shift_types = raw_data["shift_types"]

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
        for patient in raw_data["patients"]:
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
        for nurse in raw_data["nurses"]:
            self.nurse_dict[nurse["id"]] = {
                "skill_level": nurse["skill_level"],
                "working_shifts": self.nurse_working_shifts(nurse)
            }

        # Some general data items to store to stop the heuristics generating these every time
        self.all_non_mandatory_patients = [patient_id for patient_id in self.patient_dict if not self.patient_dict[patient_id]["mandatory"]]
        self.all_nurses = [nurse_id for nurse_id in self.nurse_dict]
    
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