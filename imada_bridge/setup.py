"""
Build the IMADA bridge extension (_imada).

From the repo root:
    python imada_bridge/setup.py build_ext --inplace

Requirements: pybind11 (pip/uv), and a C++20 compiler (GCC 11+, Clang 14+,
MSVC 2019 16.8+), since the IMADA move generators use C++20 coroutines.

The IMADA repo is expected next to ours (../ihtc2024-imada-submission);
set IMADA_REPO to override. Their sources are compiled as-is.
"""

import glob
import os
import sys

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
IMADA = os.environ.get(
    "IMADA_REPO", os.path.join(os.path.dirname(REPO_ROOT), "ihtc2024-imada-submission")
)
IMADA_SRC = os.path.join(IMADA, "src")
if not os.path.isdir(IMADA_SRC):
    sys.exit(f"IMADA sources not found at {IMADA_SRC}. Set IMADA_REPO.")

# Their solver's entry point and search algorithms are not needed.
EXCLUDE = {"main.cpp", "algorithms.cpp", "perturbator.cpp"}
imada_sources = sorted(
    f for f in glob.glob(os.path.join(IMADA_SRC, "*.cpp")) if os.path.basename(f) not in EXCLUDE
)

if sys.platform == "win32":
    extra = ["/std:c++20", "/O2", "/EHsc"]
else:
    # -O3 rather than their -Ofast: fast-math in a shared library can change
    # floating point behaviour for the whole Python process (numpy included).
    extra = ["-std=c++20", "-O3"]

ext = Pybind11Extension(
    "_imada",
    [os.path.join(HERE, "bindings.cpp")] + imada_sources,
    include_dirs=[IMADA_SRC],
    extra_compile_args=extra,
)

# Build into imada_bridge/ regardless of the working directory.
os.chdir(HERE)
setup(name="imada_bridge", ext_modules=[ext], cmdclass={"build_ext": build_ext})
