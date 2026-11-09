// pybind11 bridge to the SDU-IMADA IHTC-2024 solver's move generators.
//
// The IMADA sources (https://github.com/Arthod/ihtc2024-imada-submission) are
// compiled unmodified into this extension. This file only:
//   1. loads an instance with their Problem::from_textio,
//   2. converts our solution dict into their SolutionData,
//   3. draws a move with their MoveGenerator*::next() and applies it with
//      their Move::make(),
//   4. converts their SolutionData back into our solution format.
//
// One adaptation is needed. IMADA's model assumes every (room, day, shift)
// always has exactly one nurse; MoveSetNurse::make indexes the outgoing nurse
// directly. Our solutions may leave a room uncovered, so the nurse-room table
// gets one extra placeholder slot ("no nurse") at index problem.nurses.size().
// Their code never picks that slot itself, and it is dropped on export.

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <array>
#include <iostream>
#include <map>
#include <memory>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <vector>

#include "move.h"
#include "move_generator.h"
#include "problem.h"
#include "solution.h"
#include "solution_data.h"

namespace py = pybind11;

// Their loader prints to std::cout; keep that out of our logs.
struct CoutSilencer {
    std::ostringstream sink;
    std::streambuf* old = nullptr;
    CoutSilencer() { old = std::cout.rdbuf(sink.rdbuf()); }
    void restore() {
        if (old) {
            std::cout.rdbuf(old);
            old = nullptr;
        }
    }
    ~CoutSilencer() { restore(); }
};

static int lookup(const std::map<std::string, int>& m, const std::string& key, const char* what) {
    auto it = m.find(key);
    if (it == m.end()) {
        throw py::key_error(std::string("Unknown ") + what + " id: " + key);
    }
    return it->second;
}

class Engine {
public:
    // Declaration order matters: generators hold references to gen and problem.
    std::mt19937 gen;
    CoutSilencer silencer;
    Problem problem;  // built in place: their move constructor is declared but not defined
    int no_nurse;

    std::map<std::string, int> patient_index, room_index, theater_index, nurse_index, shift_index;

    std::unique_ptr<SolutionData> sd;
    std::unique_ptr<Solution> sol;

    std::vector<std::unique_ptr<MoveGenerator>> owned;
    std::map<std::string, MoveGenerator*> generators;
    std::array<std::pair<MoveGenerator*, double>, 8> union_weights;
    std::unique_ptr<MoveGeneratorUnion> union_generator;

    Engine(const std::string& instance_path, unsigned int seed)
        : gen(seed), problem(Problem::from_textio(instance_path, gen)) {
        silencer.restore();
        no_nurse = static_cast<int>(problem.nurses.size());

        for (int i = 0; i < (int)problem.patients.size(); i++) patient_index[problem.patients[i].id] = i;
        for (int i = 0; i < (int)problem.rooms.size(); i++) room_index[problem.rooms[i].id] = i;
        for (int i = 0; i < (int)problem.operating_theaters.size(); i++) theater_index[problem.operating_theaters[i].id] = i;
        for (int i = 0; i < (int)problem.nurses.size(); i++) nurse_index[problem.nurses[i].id] = i;
        for (int i = 0; i < (int)problem.shift_types.size(); i++) shift_index[problem.shift_types[i]] = i;

        // Order and weights as in IMADA src/main.cpp (SA phase).
        add("remove_optional_patient", new MoveGeneratorRemoveOptionalPatient(problem, gen), 0.5);
        add("set_patient", new MoveGeneratorSetPatient(problem, gen), 0.7);
        add("set_nurse", new MoveGeneratorSetNurse(problem, gen), 0.7);
        add("swap_patients", new MoveGeneratorSwapPatients(problem, gen), 0.8);
        add("swap_nurses_single", new MoveGeneratorSwapNursesSingle(problem, gen), 0.5);
        add("swap_nurses_all", new MoveGeneratorSwapNursesAll(problem, gen), 0.001);
        add("kick_patient", new MoveGeneratorKickPatient(problem, gen), 0.1);
        add("kick_patient_out", new MoveGeneratorKickPatientOut(problem, gen), 0.2);
        union_generator = std::make_unique<MoveGeneratorUnion>(problem, gen, union_weights);
    }

    void seed(unsigned int s) { gen.seed(s); }

    std::vector<std::string> generator_names() const {
        std::vector<std::string> names;
        for (const auto& [name, _] : generators) names.push_back(name);
        return names;
    }

    // Our solution dict -> their SolutionData
    void load(py::list patients, py::list nurses) {
        const int P = problem.patients.size();
        const int R = problem.rooms.size();
        const int D = problem.days;
        const int S = problem.num_shift_types;
        const int N = problem.nurses.size();

        std::unordered_set<int> scheduled;
        std::vector<int> admission(P, -1), room(P, -1), theater(P, -1);
        for (auto item : patients) {
            py::dict p = item.cast<py::dict>();
            py::object day = p["admission_day"];
            if (py::isinstance<py::str>(day)) continue;  // "none"
            int i = lookup(patient_index, p["id"].cast<std::string>(), "patient");
            admission[i] = day.cast<int>();
            room[i] = lookup(room_index, p["room"].cast<std::string>(), "room");
            theater[i] = lookup(theater_index, p["operating_theater"].cast<std::string>(), "theater");
            scheduled.insert(i);
        }

        std::vector<int> room_day_shift_nurse(R * D * S, no_nurse);
        std::vector<std::vector<std::vector<std::vector<int>>>> nurse_day_shift_rooms(
            N + 1, std::vector<std::vector<std::vector<int>>>(D, std::vector<std::vector<int>>(S)));
        for (auto item : nurses) {
            py::dict n = item.cast<py::dict>();
            int ni = lookup(nurse_index, n["id"].cast<std::string>(), "nurse");
            for (auto a_item : n["assignments"].cast<py::list>()) {
                py::dict a = a_item.cast<py::dict>();
                int d = a["day"].cast<int>();
                int s = lookup(shift_index, a["shift"].cast<std::string>(), "shift");
                for (auto r_item : a["rooms"].cast<py::list>()) {
                    int r = lookup(room_index, r_item.cast<std::string>(), "room");
                    nurse_day_shift_rooms[ni][d][s].push_back(r);
                    int idx = r * D * S + d * S + s;
                    if (room_day_shift_nurse[idx] == no_nurse) room_day_shift_nurse[idx] = ni;
                }
            }
        }

        sol.reset();  // Solution holds a reference to sd
        sd = std::make_unique<SolutionData>(problem, scheduled, admission, room, theater,
                                            room_day_shift_nurse, nurse_day_shift_rooms);
        sol = std::make_unique<Solution>(problem, *sd);
    }

    // Draw with their generator's next() and apply with their make().
    // Returns false if every draw was invalid (their next() returned nullptr).
    bool apply(const std::string& name, int max_tries) {
        if (!sol) throw std::runtime_error("Engine.apply called before Engine.load");
        MoveGenerator* g = nullptr;
        if (name == "union") {
            g = union_generator.get();
        } else {
            auto it = generators.find(name);
            if (it == generators.end()) throw py::key_error("Unknown IMADA generator: " + name);
            g = it->second;
        }
        for (int t = 0; t < max_tries; t++) {
            std::unique_ptr<Move> move = g->next(*sol);
            if (move) {
                move->make(*sd);
                return true;
            }
        }
        return false;
    }

    // Their SolutionData -> our solution format
    py::dict export_solution() const {
        if (!sd) throw std::runtime_error("Engine.export_solution called before Engine.load");
        py::list patients;
        for (int i = 0; i < (int)problem.patients.size(); i++) {
            py::dict p;
            p["id"] = problem.patients[i].id;
            if (sd->patients_scheduled.count(i)) {
                p["admission_day"] = sd->patient_admission_days[i];
                p["room"] = problem.rooms[sd->patient_room_ids[i]].id;
                p["operating_theater"] = problem.operating_theaters[sd->patient_operating_theaters[i]].id;
            } else {
                p["admission_day"] = "none";
            }
            patients.append(p);
        }

        py::list nurses;
        for (int n = 0; n < (int)problem.nurses.size(); n++) {  // placeholder slot excluded
            py::list assignments;
            for (int d = 0; d < problem.days; d++) {
                for (int s = 0; s < problem.num_shift_types; s++) {
                    const auto& rooms = sd->nurse_day_shift_rooms[n][d][s];
                    if (rooms.empty()) continue;
                    py::list room_ids;
                    for (int r : rooms) room_ids.append(problem.rooms[r].id);
                    py::dict a;
                    a["day"] = d;
                    a["shift"] = problem.shift_types[s];
                    a["rooms"] = room_ids;
                    assignments.append(a);
                }
            }
            if (py::len(assignments) == 0) continue;
            py::dict nd;
            nd["id"] = problem.nurses[n].id;
            nd["assignments"] = assignments;
            nurses.append(nd);
        }

        py::dict out;
        out["patients"] = patients;
        out["nurses"] = nurses;
        return out;
    }

private:
    void add(const std::string& name, MoveGenerator* g, double weight) {
        union_weights[owned.size()] = {g, weight};
        owned.emplace_back(g);
        generators[name] = g;
    }
};

PYBIND11_MODULE(_imada, m) {
    m.doc() = "Bridge to the SDU-IMADA IHTC-2024 move generators (compiled from their unmodified C++ sources)";
    py::class_<Engine>(m, "Engine")
        .def(py::init<const std::string&, unsigned int>(), py::arg("instance_path"), py::arg("seed") = 0)
        .def("seed", &Engine::seed)
        .def("generator_names", &Engine::generator_names)
        .def("load", &Engine::load, py::arg("patients"), py::arg("nurses"))
        .def("apply", &Engine::apply, py::arg("name"), py::arg("max_tries") = 20)
        .def("export_solution", &Engine::export_solution);
}
