# IHTC2024
Development space for the IHTC 2024.

https://ihtc2024.github.io/

## Development team and contributions

- Matthew Davison (Team leader)

## Running the validator or the optimiser

To run for an instance/solution pair use the following:

```bash
> ./IHTP_Validator.exe input_file.json sol_file.json
```

To run the optimiser for an instance use the following:

```bash
> python main.py input_file.json
```

To fix a seed (for example, 1234) for random generation then use the following:

```bash
> python main.py input_file.json --seed 1234
```

To specify an output folder (for example, solutions) then use the following:

```bash
> python main.py input_file.json --output_folder solutions
```

## Data format

```json
{
  "days": 21,
  "skill_levels": 3,
  "shift_types": [
    "early",
    "late",
    "night"
  ],
  "age_groups": [
    "infant",
    "adult",
    "elderly"
  ],
  "occupants": [
    {
      "id": "a0",
      "gender": "A",
      "age_group": "elderly",
      "length_of_stay": 4,
      "workload_produced": [3,3,1,1,1,1,1,1,1,1,2,1],
      "skill_level_required": [1,0,0,0,2,0,1,1,1,1,0,0],
      "room_id": "r4"
    }
  ],
  "patients": [
    {
      "id": "p00",
      "mandatory": false,
      "gender": "A",
      "age_group": "elderly",
      "length_of_stay": 3,
      "surgery_release_day": 3,
      "surgery_duration": 120,
      "surgeon_id": "s0",
      "incompatible_room_ids": [],
      "workload_produced": [3,2,2,2,3,1,2,2,2],
      "skill_level_required": [0,2,0,0,0,0,2,2,0]
    }
  ],
  "surgeons": [
    {
      "id": "s0",
      "max_surgery_time": [0,480,0,480,360,0,0,600,360,0,
                           0,480,0,600,480,0,480,480,0,480,
                           0]
    }
  ],
  "operating_theaters": [
    {
      "id": "t0",
      "availability": [600,720,600,600,480,720,600,600,600,600,
                       0,600,720,480,720,0,720,600,720,720,
                       600]
    }
  ]
  "rooms": [
    {
      "id": "r0",
      "capacity": 3
    }
  ]
  "nurses": [
    {
      "id": "n00",
      "skill_level": 1,
      "working_shifts": [
        {"day": 0, "shift": "late", "max_load": 12},
        {"day": 1, "shift": "late", "max_load": 12},
        {"day": 2, "shift": "night", "max_load": 12},
        {"day": 4, "shift": "night", "max_load": 12},
        {"day": 5, "shift": "night", "max_load": 12},
        {"day": 7, "shift": "night", "max_load": 12},
        {"day": 9, "shift": "early", "max_load": 12},
        {"day": 10, "shift": "early", "max_load": 12},
        {"day": 11, "shift": "early", "max_load": 12},
        {"day": 12, "shift": "early", "max_load": 12},
        {"day": 13, "shift": "early", "max_load": 12},
        {"day": 14, "shift": "early", "max_load": 12},
        {"day": 15, "shift": "early", "max_load": 12},
        {"day": 16, "shift": "late", "max_load": 12},
        {"day": 17, "shift": "late", "max_load": 12},
        {"day": 18, "shift": "late", "max_load": 12},
        {"day": 19, "shift": "late", "max_load": 12},
        {"day": 20, "shift": "late", "max_load": 12}
      ]
    }
  ]
  "weights": {
    "room_mixed_age": 5,
    "room_nurse_skill": 1,
    "continuity_of_care": 5,
    "nurse_eccessive_workload": 1,
    "open_operating_theater": 30,
    "surgeon_transfer": 1,
    "patient_delay": 5,
    "unscheduled_optional": 150
  }
}
```

## Solution format

```json
{
  "patients": [
    {
      "id": "p00",
      "admission_day": 3,
      "room": "r3",
      "operating_theater": "t1"
    },
    {
      "id": "p01",
      "admission_day": "none"
    }
    ],
    "nurses": [
    {
      "id": "n01",
      "assignments": [
        {"day": 2, "shift": "late", "rooms": ["r3"]},
        {"day": 18, "shift": "night", "rooms": ["r1","r2","r3"]}
      ]
    }
  ]
```

## Hard constraints

**H1 -** No gender mix: Patients of different genders may not share a room on any day.

**H2 -** Compatible rooms: Patients can only be assigned to one of their compatible rooms.

**H3 -** Surgeon overtime: The maximum daily surgery time of a surgeon must not be exceeded.

**H4 -** OT overtime: The duration of all surgeries allocated to an OT on a day must not exceed its maximum capacity.

**H5 -** Mandatory versus optional patients: All mandatory patients must be admitted within the scheduling period, whereas optional patients may be postponed to future scheduling periods.

**H6 -** Admission day: A patient can be admitted on any day from their release date to their due date. Given that optional patients do not have a due date, they can be admitted on any day after their release date.

**H7 -** Room capacity: The number of patients in each room in each day cannot exceed the capacity of the room.

## Boundary data

Some patients are already in hospital but are assumed to have had their operation already.