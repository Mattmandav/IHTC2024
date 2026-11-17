#ifndef RUN_STATS_H
#define RUN_STATS_H

// Instrumentation for running the SDU-IMADA IHTC-2024 solver on our hardware.
// Added by the IHTC2024 team (Mattmandav/IHTC2024), not part of the original
// solver. It only counts and records: no search decision reads these values.
//
// The solver runs four independent searches in parallel threads (run1..run4 in
// main.cpp), so every counter is thread_local and reported per thread.
//
// Definitions (a "move" is one candidate neighbour, delta-evaluated):
//   sa_iterations   moves evaluated by simulated annealing (sa_plus)
//   sa_accepted     of those, moves applied (improving, sideways or worsening)
//   sa_improving    of those, moves that strictly improved the lexicographic
//                   (hard violations, soft cost) objective
//   sa_new_best     times SA found a new best solution
//   ls_iterations   moves evaluated by the local search inside ILS (fi_plus)
//   ls_improving    of those, moves applied (fi_plus only applies improving moves)
//   ils_iterations  ILS cycles (local search + perturbation)
//   ils_new_best    ILS cycles that ended in a strictly better solution
//   feasible_*      first solution with no hard violations: seconds since the
//                   thread's search started, moves evaluated before it, soft cost

#include <chrono>
#include <fstream>
#include <string>
#include <vector>

#include "json.hpp"
#include "solution.h"

struct RunStats {
    int initial_hard = -1;
    int initial_soft = -1;
    bool feasible_found = false;
    double feasible_seconds = -1;
    long long feasible_iteration = -1;
    int feasible_soft = -1;
    long long sa_iterations = 0;
    long long sa_accepted = 0;
    long long sa_improving = 0;
    long long sa_new_best = 0;
    long long ls_iterations = 0;
    long long ls_improving = 0;
    long long ils_iterations = 0;
    long long ils_new_best = 0;
    int final_hard = -1;
    int final_soft = -1;
    double seconds = 0;
    std::chrono::steady_clock::time_point start;
};

inline thread_local RunStats run_stats;

inline void stats_check_feasible(const Solution& s) {
    if (!run_stats.feasible_found && s.evaluation.values[0] == 0) {
        run_stats.feasible_found = true;
        run_stats.feasible_seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - run_stats.start).count();
        run_stats.feasible_iteration = run_stats.sa_iterations + run_stats.ls_iterations;
        run_stats.feasible_soft = s.evaluation.values[1];
    }
}

inline void stats_begin(const Solution& s) {
    run_stats = RunStats();
    run_stats.start = std::chrono::steady_clock::now();
    run_stats.initial_hard = s.evaluation.values[0];
    run_stats.initial_soft = s.evaluation.values[1];
    stats_check_feasible(s);
}

inline RunStats stats_end(const Solution& s) {
    run_stats.final_hard = s.evaluation.values[0];
    run_stats.final_soft = s.evaluation.values[1];
    run_stats.seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - run_stats.start).count();
    return run_stats;
}

inline void write_run_stats(const std::string& path, unsigned seed,
                            const std::vector<unsigned>& thread_seeds,
                            const std::vector<RunStats>& stats, int best_thread,
                            double load_seconds, double total_seconds) {
    nlohmann::json out;
    out["seed"] = seed;
    out["best_thread"] = best_thread;
    out["load_seconds"] = load_seconds;
    out["total_seconds"] = total_seconds;
    out["threads"] = nlohmann::json::array();
    for (size_t i = 0; i < stats.size(); i++) {
        const RunStats& r = stats[i];
        out["threads"].push_back({
            {"thread", i + 1},
            {"thread_seed", thread_seeds[i]},
            {"initial_hard", r.initial_hard},
            {"initial_soft", r.initial_soft},
            {"feasible_found", r.feasible_found},
            {"feasible_seconds", r.feasible_seconds},
            {"feasible_iteration", r.feasible_iteration},
            {"feasible_soft", r.feasible_soft},
            {"sa_iterations", r.sa_iterations},
            {"sa_accepted", r.sa_accepted},
            {"sa_improving", r.sa_improving},
            {"sa_new_best", r.sa_new_best},
            {"ls_iterations", r.ls_iterations},
            {"ls_improving", r.ls_improving},
            {"ils_iterations", r.ils_iterations},
            {"ils_new_best", r.ils_new_best},
            {"final_hard", r.final_hard},
            {"final_soft", r.final_soft},
            {"seconds", r.seconds},
        });
    }
    std::ofstream(path) << out.dump(2) << std::endl;
}

#endif
