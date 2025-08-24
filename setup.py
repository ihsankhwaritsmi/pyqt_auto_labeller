import setuptools

# Available at setup time due to pyproject.toml
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir

import sys

__version__ = "0.0.1"

# The main interface is through Pybind11Extension.
# * You can pass in a list of sources, e.g. `glob.glob("src/*.cpp")`,
#   or a list of `SourceFile` objects that contains additional
#   information like compile flags.
#
# * You can also pass in `define_macros`, for example to set the
#   version number.
#
# * By default, Pybind11Extension adds all necessary include paths for
#   pybind11, but you can add your own via `include_dirs`.
#
# * You can also specify additional link libraries / library directories.
#
# See https://pybind11.readthedocs.io/en/stable/reference/setup_helpers.html
# for more details.

ext_modules = [
    Pybind11Extension("bbox_utils",
        ["src/bbox_utils.cpp"],
        define_macros=[('VERSION_INFO', __version__)],
        ),
]

setuptools.setup(
    name="bbox_utils",
    version=__version__,
    author="Cline",
    author_email="cline@example.com",
    description="A small example package using pybind11",
    long_description="",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
)
