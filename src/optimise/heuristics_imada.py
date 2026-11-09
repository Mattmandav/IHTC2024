"""
Low level heuristics ported from the SDU-IMADA IHTC-2024 solver.

Source: https://github.com/Arthod/ihtc2024-imada-submission
    src/move_generator.cpp  (the MoveGenerator*::next() methods)
    src/problem.cpp         (allowed values and candidate patient lists)
    src/move.cpp            (MoveSetPatient / MoveSetNurse semantics)

Citation: Othman & Chiarandini (2026), "A multi-neighborhood, lexicographic
local search algorithm for the Integrated Healthcare Timetabling Competition
2024", Operations Research, Data Analytics and Logistics 47:200513.
Their code is Apache-2.0 licensed.

The IMADA solver is C++, so these are Python ports of the random-draw
("next") version of each of their 8 move generators. Every public function
here has the same signature as the moves in heuristics.py:

    move(data, solution) -> solution

so this module can be passed to the optimiser in place of (or alongside)
src.optimise.heuristics.

Conventions kept from heuristics.py:
  * the solution dict is modified in place and returned;
  * unscheduled patients are kept as {"id": ..., "admission_day": "none"};
  * room/theater/surgeon allocations are refreshed after every move;
  * all helper names start with "__" so the optimiser's dir()-based
    discovery only picks up the moves.

Differences from IMADA worth knowing:
  * IMADA's next() returns nullptr on an invalid draw and the search simply
    draws again (cheap for them). Here each call to the validator is
    expensive, so each move retries up to __MAX_TRIES times before giving up
    and returning the solution unchanged.
  * IMADA assumes every (room, day, shift) always has exactly one nurse.
    Our solutions may have zero or several, so SetNurse removes the room from
    every nurse currently covering it before assigning the new one.
"""

import os
import random as rd
import re
import warnings

import src.optimise.heuristics as __ours

__MAX_TRIES = 20

# Generator weights IMADA use in their simulated annealing phase
# (src/main.cpp, first configuration). Used by imada_weighted_union and
# available to anyone who wants to bias selection in the optimiser.
IMADA_WEIGHTS = {
    "imada_remove_optional_patient": 0.5,
    "imada_set_patient": 0.7,
    "imada_set_nurse": 0.7,
    "imada_swap_patients": 0.8,
    "imada_swap_nurses_single": 0.5,
    "imada_swap_nurses_all": 0.001,
    "imada_kick_patient": 0.1,
    "imada_kick_patient_out": 0.2,
}

# IMADA class name -> function in this module
IMADA_GENERATOR_MAP = {
    "MoveGeneratorRemoveOptionalPatient": "imada_remove_optional_patient",
    "MoveGeneratorSetPatient": "imada_set_patient",
    "MoveGeneratorSetNurse": "imada_set_nurse",
    "MoveGeneratorSwapPatients": "imada_swap_patients",
    "MoveGeneratorSwapNursesSingle": "imada_swap_nurses_single",
    "MoveGeneratorSwapNursesAll": "imada_swap_nurses_all",
    "MoveGeneratorKickPatient": "imada_kick_patient",
    "MoveGeneratorKickPatientOut": "imada_kick_patient_out",
}


"""
LOCATING AND CHECKING THE IMADA SOURCE
"""


def __imada_repo_path():
    """
    The IMADA repo is expected to sit next to ours:
        <parent>/IHTC2024/src/optimise/heuristics_imada.py
        <parent>/ihtc2024-imada-submission/
    Override with the IMADA_REPO environment variable if it lives elsewhere.
    """
    if os.environ.get("IMADA_REPO"):
        return os.environ["IMADA_REPO"]
    here = os.path.dirname(os.path.abspath(__file__))
    our_root = os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.join(os.path.dirname(our_root), "ihtc2024-imada-submission")


def __check_imada_source():
    """
    Read move_generator.h from the IMADA repo and warn if their set of move
    generators differs from what has been ported here. Silent if the repo is
    absent: the ported moves do not need it to run.
    """
    header = os.path.join(__imada_repo_path(), "src", "move_generator.h")
    if not os.path.isfile(header):
        return
    with open(header) as f:
        text = f.read()
    found = set(re.findall(r"class\s+(MoveGenerator\w+)\s*:", text))
    found.discard("MoveGeneratorUnion")
    ported = set(IMADA_GENERATOR_MAP)
    if found != ported:
        warnings.warn(
            "IMADA move generators have changed. "
            f"Not ported: {sorted(found - ported)}. "
            f"No longer in IMADA: {sorted(ported - found)}."
        )


__check_imada_source()


"""
PRECOMPUTED PROBLEM DATA (mirrors IMADA's Problem helpers in problem.cpp)
"""


def __cache(data):
    """
    Build once per Data object and store on it. Holds:
      allowed[p]      : list of (room, theater, day) IMADA allow for patient p
      allowed_set[p]  : same as a set
      kickable[p]     : patients whose allowed values overlap with p's
      day_shift_nurses: (day, shift) -> nurses working that shift
    """
    cache = getattr(data, "_imada_cache", None)
    if cache is not None:
        return cache

    raw = data.data
    ndays = data.ndays
    rooms = raw["rooms"]
    theaters = raw["operating_theaters"]
    surgeons = {s["id"]: s for s in raw["surgeons"]}

    # Occupant load and genders per (room, day)
    occ_count = {(r["id"], d): 0 for r in rooms for d in range(ndays)}
    occ_gender = {(r["id"], d): set() for r in rooms for d in range(ndays)}
    for o in raw["occupants"]:
        for d in range(min(o["length_of_stay"], ndays)):
            occ_count[(o["room_id"], d)] += 1
            occ_gender[(o["room_id"], d)].add(o["gender"])
    capacity = {r["id"]: r["capacity"] for r in rooms}

    allowed = {}
    for p in raw["patients"]:
        pid = p["id"]
        start = p["surgery_release_day"]
        end = p["surgery_due_day"] if p["mandatory"] else ndays - 1
        surgeon = surgeons[p["surgeon_id"]]
        values = []
        for r in rooms:
            rid = r["id"]
            if rid in p["incompatible_room_ids"]:
                continue
            for d in range(start, end + 1):
                if surgeon["max_surgery_time"][d] < p["surgery_duration"]:
                    continue
                if occ_count[(rid, d)] >= capacity[rid]:
                    continue
                if occ_gender[(rid, d)] - {p["gender"]}:
                    continue
                for t in theaters:
                    if t["availability"][d] < p["surgery_duration"]:
                        continue
                    values.append((rid, t["id"], d))
        allowed[pid] = values

    allowed_set = {pid: set(v) for pid, v in allowed.items()}

    kickable = {}
    pids = list(allowed)
    for i in pids:
        kickable[i] = [
            j for j in pids if j != i and not allowed_set[i].isdisjoint(allowed_set[j])
        ]

    day_shift_nurses = {}
    for n in raw["nurses"]:
        for ws in n["working_shifts"]:
            day_shift_nurses.setdefault((ws["day"], ws["shift"]), []).append(n["id"])

    cache = {
        "allowed": allowed,
        "allowed_set": allowed_set,
        "kickable": kickable,
        "day_shift_nurses": day_shift_nurses,
        "room_ids": [r["id"] for r in rooms],
    }
    data._imada_cache = cache
    return cache


"""
SOLUTION ACCESS HELPERS
"""


def __patient_entries(solution):
    return {p["id"]: p for p in solution["patients"]}


def __value_of(entry):
    """(room, theater, day) for a scheduled patient, None if unscheduled."""
    if entry is None or entry.get("admission_day", "none") == "none":
        return None
    return (entry["room"], entry["operating_theater"], entry["admission_day"])


def __set_patient(solution, entries, pid, value):
    """
    MoveSetPatient. value is (room, theater, day), or None to unschedule.
    Patients missing from the list (e.g. after heuristics.remove_patient)
    are added back.
    """
    if value is None:
        new_entry = {"id": pid, "admission_day": "none"}
    else:
        room, theater, day = value
        new_entry = {
            "id": pid,
            "admission_day": day,
            "room": room,
            "operating_theater": theater,
        }
    if pid in entries:
        entries[pid].clear()
        entries[pid].update(new_entry)
    else:
        solution["patients"].append(new_entry)
        entries[pid] = new_entry


def __nurse_rooms(solution, nurse_id, day, shift):
    """Rooms a nurse covers on (day, shift); empty list if none."""
    for n in solution["nurses"]:
        if n["id"] == nurse_id:
            for a in n["assignments"]:
                if a["day"] == day and a["shift"] == shift:
                    return list(a["rooms"])
    return []


def __room_nurses(solution, room, day, shift):
    return [
        n["id"]
        for n in solution["nurses"]
        for a in n["assignments"]
        if a["day"] == day and a["shift"] == shift and room in a["rooms"]
    ]


def __set_nurse(solution, nurse_id, room, day, shift):
    """
    MoveSetNurse: the nurse becomes the (only) nurse for room on (day, shift).
    """
    # Remove the room from whoever currently covers it
    for n in solution["nurses"]:
        for a in n["assignments"]:
            if a["day"] == day and a["shift"] == shift and room in a["rooms"]:
                a["rooms"] = [r for r in a["rooms"] if r != room]

    # Find or create the nurse entry and assignment
    nurse_entry = next((n for n in solution["nurses"] if n["id"] == nurse_id), None)
    if nurse_entry is None:
        nurse_entry = {"id": nurse_id, "assignments": []}
        solution["nurses"].append(nurse_entry)
    for a in nurse_entry["assignments"]:
        if a["day"] == day and a["shift"] == shift:
            if room not in a["rooms"]:
                a["rooms"].append(room)
            return
    nurse_entry["assignments"].append({"day": day, "shift": shift, "rooms": [room]})


def __finish(data, solution):
    if "room_allocation" in solution:
        solution = __ours.__update_allocations__(data, solution)
    return solution


def __random_day_shift(data):
    return rd.randrange(data.ndays), rd.choice(data.shift_types)


def __two_nurses(cache, day, shift):
    nurses = cache["day_shift_nurses"].get((day, shift), [])
    if len(nurses) < 2:
        return None
    return rd.sample(nurses, 2)


"""
PATIENT MOVES
"""


def imada_remove_optional_patient(data, solution):
    """MoveGeneratorRemoveOptionalPatient: unschedule a random optional patient."""
    entries = __patient_entries(solution)
    for _ in range(__MAX_TRIES):
        pid = rd.choice(data.all_non_mandatory_patients)
        if __value_of(entries.get(pid)) is None:
            continue
        __set_patient(solution, entries, pid, None)
        return __finish(data, solution)
    return solution


def imada_set_patient(data, solution):
    """
    MoveGeneratorSetPatient: give a random patient (scheduled or not) a random
    allowed (room, theater, day). Covers insert, relocate and re-time.
    """
    cache = __cache(data)
    entries = __patient_entries(solution)
    for _ in range(__MAX_TRIES):
        pid = rd.choice(list(data.patient_dict))
        options = cache["allowed"][pid]
        if not options:
            continue
        __set_patient(solution, entries, pid, rd.choice(options))
        return __finish(data, solution)
    return solution


def imada_swap_patients(data, solution):
    """
    MoveGeneratorSwapPatients: two scheduled patients exchange
    (room, theater, day), if each is allowed at the other's value.
    """
    cache = __cache(data)
    entries = __patient_entries(solution)
    pids = list(data.patient_dict)
    for _ in range(__MAX_TRIES):
        p1, p2 = rd.sample(pids, 2)
        v1, v2 = __value_of(entries.get(p1)), __value_of(entries.get(p2))
        if v1 is None or v2 is None:
            continue
        if v2 not in cache["allowed_set"][p1] or v1 not in cache["allowed_set"][p2]:
            continue
        __set_patient(solution, entries, p1, v2)
        __set_patient(solution, entries, p2, v1)
        return __finish(data, solution)
    return solution


def imada_kick_patient(data, solution):
    """
    MoveGeneratorKickPatient: p1 takes p2's (room, theater, day) and p2 is
    moved to a random allowed value of its own.
    """
    cache = __cache(data)
    entries = __patient_entries(solution)
    pids = list(data.patient_dict)
    for _ in range(__MAX_TRIES):
        p1, p2 = rd.sample(pids, 2)
        v1, v2 = __value_of(entries.get(p1)), __value_of(entries.get(p2))
        if v1 is None or v2 is None:
            continue
        if v2 not in cache["allowed_set"][p1] or not cache["allowed"][p2]:
            continue
        __set_patient(solution, entries, p1, v2)
        __set_patient(solution, entries, p2, rd.choice(cache["allowed"][p2]))
        return __finish(data, solution)
    return solution


def imada_kick_patient_out(data, solution):
    """
    MoveGeneratorKickPatientOut: p1 takes the (room, theater, day) of a
    scheduled optional patient p2, and p2 is unscheduled.
    """
    cache = __cache(data)
    entries = __patient_entries(solution)
    pids = list(data.patient_dict)
    optional = data.all_non_mandatory_patients
    if not optional:
        return solution
    for _ in range(__MAX_TRIES):
        p1 = rd.choice(pids)
        p2 = rd.choice(optional)
        if p1 == p2:
            continue
        v1, v2 = __value_of(entries.get(p1)), __value_of(entries.get(p2))
        if v1 is None or v2 is None:
            continue
        if v2 not in cache["allowed_set"][p1]:
            continue
        __set_patient(solution, entries, p1, v2)
        __set_patient(solution, entries, p2, None)
        return __finish(data, solution)
    return solution


"""
NURSE MOVES
"""


def imada_set_nurse(data, solution):
    """
    MoveGeneratorSetNurse: for a random (room, day, shift), assign a random
    nurse working that shift who is not already covering it.
    """
    cache = __cache(data)
    for _ in range(__MAX_TRIES):
        room = rd.choice(cache["room_ids"])
        day, shift = __random_day_shift(data)
        nurses = cache["day_shift_nurses"].get((day, shift), [])
        if not nurses:
            continue
        nurse = rd.choice(nurses)
        if __room_nurses(solution, room, day, shift) == [nurse]:
            continue
        __set_nurse(solution, nurse, room, day, shift)
        return __finish(data, solution)
    return solution


def imada_swap_nurses_single(data, solution):
    """
    MoveGeneratorSwapNursesSingle: two nurses on the same (day, shift)
    exchange one room each.
    """
    cache = __cache(data)
    for _ in range(__MAX_TRIES):
        day, shift = __random_day_shift(data)
        pair = __two_nurses(cache, day, shift)
        if pair is None:
            continue
        n1, n2 = pair
        rooms1 = __nurse_rooms(solution, n1, day, shift)
        rooms2 = __nurse_rooms(solution, n2, day, shift)
        if not rooms1 or not rooms2:
            continue
        r1, r2 = rd.choice(rooms1), rd.choice(rooms2)
        __set_nurse(solution, n1, r2, day, shift)
        __set_nurse(solution, n2, r1, day, shift)
        return __finish(data, solution)
    return solution


def imada_swap_nurses_all(data, solution):
    """
    MoveGeneratorSwapNursesAll: two nurses on the same (day, shift) exchange
    their entire room sets.
    """
    cache = __cache(data)
    for _ in range(__MAX_TRIES):
        day, shift = __random_day_shift(data)
        pair = __two_nurses(cache, day, shift)
        if pair is None:
            continue
        n1, n2 = pair
        rooms1 = __nurse_rooms(solution, n1, day, shift)
        rooms2 = __nurse_rooms(solution, n2, day, shift)
        if len(rooms1) + len(rooms2) < 2:
            continue
        for r in rooms1:
            __set_nurse(solution, n2, r, day, shift)
        for r in rooms2:
            __set_nurse(solution, n1, r, day, shift)
        return __finish(data, solution)
    return solution


"""
WEIGHTED UNION (MoveGeneratorUnion)
"""


def imada_weighted_union(data, solution):
    """
    Pick one of the moves above using IMADA's SA weights. Useful with
    heuristic_selection="random", where uniform selection would otherwise
    over-use imada_swap_nurses_all (weight 0.001 in IMADA).
    """
    names = list(IMADA_WEIGHTS)
    name = rd.choices(names, weights=[IMADA_WEIGHTS[n] for n in names])[0]
    return globals()[name](data, solution)
