"""
Low level heuristics from the SDU-IMADA IHTC-2024 solver, called through a
compiled bridge to their original C++ code.

Source: https://github.com/Arthod/ihtc2024-imada-submission (Apache-2.0)
Citation: Othman & Chiarandini (2026), "A multi-neighborhood, lexicographic
local search algorithm for the Integrated Healthcare Timetabling Competition
2024", Operations Research, Data Analytics and Logistics 47:200513.

No move logic lives here. Each move:
  1. loads our solution into IMADA's SolutionData (imada_bridge/bindings.cpp),
  2. draws a move with their MoveGenerator*::next() and applies Move::make(),
  3. exports the result back to our solution format.

Build the bridge first (from the repo root):
    python imada_bridge/setup.py build_ext --inplace

Every public function has the same signature as the moves in heuristics.py:
    move(data, solution) -> solution
All helper names start with "__" so the optimiser's dir()-based discovery
only picks up the moves.
"""

import hashlib
import json
import os
import random as rd
import tempfile

import src.optimise.heuristics as __ours

try:
    from imada_bridge import _imada as __bridge
except ImportError as __err:
    raise ImportError(
        "The IMADA bridge is not built. From the repo root run:\n"
        "    python imada_bridge/setup.py build_ext --inplace\n"
        f"(original error: {__err})"
    )

# Draws per move before giving up. IMADA's generators return nothing for an
# invalid draw and their search just draws again; redrawing in C++ costs
# microseconds, whereas returning an unchanged solution wastes a validator call.
__MAX_TRIES = 1000

# One engine per process, keyed by instance content.
__ENGINE = None
__ENGINE_KEY = None


def __prepare__(data):
    """
    Build the engine for this instance. The optimiser calls this once in the
    parent process, so that with the default "fork" start method on Linux the
    pool workers inherit a ready engine instead of each rebuilding it.
    """
    __engine(data)


def __instance_key(data):
    key = getattr(data, "_imada_key", None)
    if key is None:
        blob = json.dumps(data.data, sort_keys=True).encode()
        key = hashlib.sha1(blob).hexdigest()
        data._imada_key = key  # travels with data when it is pickled to workers
    return key


def __engine(data):
    global __ENGINE, __ENGINE_KEY
    key = __instance_key(data)
    if __ENGINE is None or __ENGINE_KEY != key:
        # Their loader reads from a file, so write the instance out once.
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data.data, f)
            # Fixed seed: it only orders IMADA's precomputed candidate lists, and
            # must not consume our RNG (otherwise runs depend on whether the
            # engine was already built). Moves are reseeded from our RNG in __run.
            __ENGINE = __bridge.Engine(path, 0)
        finally:
            os.remove(path)
        __ENGINE_KEY = key
    return __ENGINE


def __run(generator, data, solution):
    engine = __engine(data)
    engine.seed(rd.getrandbits(32))  # follow our seeding, so runs are reproducible
    engine.load(solution["patients"], solution["nurses"])
    if not engine.apply(generator, __MAX_TRIES):
        return solution
    new = engine.export_solution()
    solution["patients"] = new["patients"]
    solution["nurses"] = new["nurses"]
    if "room_allocation" in solution:
        solution = __ours.__update_allocations__(data, solution)
    return solution


"""
PATIENT MOVES
"""


def imada_remove_optional_patient(data, solution):
    """MoveGeneratorRemoveOptionalPatient: unschedule a scheduled optional patient."""
    return __run("remove_optional_patient", data, solution)


def imada_set_patient(data, solution):
    """MoveGeneratorSetPatient: give a patient a random allowed (room, theater, day)."""
    return __run("set_patient", data, solution)


def imada_swap_patients(data, solution):
    """MoveGeneratorSwapPatients: two scheduled patients exchange (room, theater, day)."""
    return __run("swap_patients", data, solution)


def imada_kick_patient(data, solution):
    """MoveGeneratorKickPatient: p1 takes p2's slot, p2 moves to a random allowed slot."""
    return __run("kick_patient", data, solution)


def imada_kick_patient_out(data, solution):
    """MoveGeneratorKickPatientOut: p1 takes an optional patient's slot, who is unscheduled."""
    return __run("kick_patient_out", data, solution)


"""
NURSE MOVES
"""


def imada_set_nurse(data, solution):
    """MoveGeneratorSetNurse: assign a working nurse to a random (room, day, shift)."""
    return __run("set_nurse", data, solution)


def imada_swap_nurses_single(data, solution):
    """MoveGeneratorSwapNursesSingle: two nurses on a shift exchange one room each."""
    return __run("swap_nurses_single", data, solution)


def imada_swap_nurses_all(data, solution):
    """MoveGeneratorSwapNursesAll: two nurses on a shift exchange all their rooms."""
    return __run("swap_nurses_all", data, solution)


"""
WEIGHTED UNION
"""


def imada_weighted_union(data, solution):
    """
    MoveGeneratorUnion with IMADA's SA weights (src/main.cpp): picks one of the
    eight generators per draw. Useful with heuristic_selection="random".
    """
    return __run("union", data, solution)
