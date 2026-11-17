#!/bin/bash
# Build the SDU-IMADA IHTC-2024 solver with our run-statistics instrumentation.
#
# Run once from the repo root, on the login node, before submitting imada_slurm.sh:
#   bash imada_solver/build.sh
#
# Their repo must sit next to ours (../ihtc2024-imada-submission), or set
# IMADA_REPO. Their sources are copied to imada_solver/build/, the
# instrumentation is applied there (their repo is never modified), and the
# solver is compiled with their own Makefile flags. Needs g++ 11+ (C++20).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
IMADA_REPO="${IMADA_REPO:-$HERE/../../ihtc2024-imada-submission}"
BUILD="$HERE/build"

if [ ! -d "$IMADA_REPO/src" ]; then
  echo "IMADA sources not found at $IMADA_REPO/src. Clone the repo there or set IMADA_REPO." >&2
  exit 1
fi

rm -rf "$BUILD"
mkdir -p "$BUILD"
cp -r "$IMADA_REPO/src" "$BUILD/src"
cp "$HERE/run_stats.h" "$BUILD/src/"
patch -s -d "$BUILD" -p0 < "$HERE/instrumentation.patch"

# Record exactly which IMADA version was built
git -C "$IMADA_REPO" rev-parse HEAD > "$BUILD/imada_commit.txt" 2>/dev/null || echo unknown > "$BUILD/imada_commit.txt"

# Their Makefile flags (-flto -lm -Ofast --std=c++20), plus -pthread for the
# four search threads on older glibc versions
SOURCES="main.cpp entities.cpp problem.cpp problem_helper.cpp solution.cpp iterable.cpp
         solution_data.cpp evaluation.cpp move_generator.cpp move.cpp utils.cpp
         evaluation_element.cpp perturbator.cpp algorithms.cpp"
(cd "$BUILD/src" && g++ -flto -Ofast --std=c++20 -pthread -o "$BUILD/imada_solver" $SOURCES -lm)

echo "Built $BUILD/imada_solver from IMADA commit $(cat "$BUILD/imada_commit.txt")"
