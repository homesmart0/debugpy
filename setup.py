#!/usr/bin/env python

# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root
# for license information.

import os
import os.path
import subprocess
import sys


pure = None
if "--pure" in sys.argv:
    pure = True
    sys.argv.remove("--pure")
elif "--universal" in sys.argv:
    pure = True
elif "--abi" in sys.argv:
    pure = False
    sys.argv.remove("--abi")


# bdist_wheel determines whether the package is pure or not based on ext_modules.
# However, all pydevd native modules are prebuilt and packaged as data, so they
# should not be in the list.
#
# The proper way to handle this is by overriding has_ext_modules. However, due to
# https://bugs.python.org/issue32957, in setuptools 57.0.0 and below, it is not
# always called when it should be, with ext_modules tested directly instead.
#
# So, for non-pure builds, we provide a customized empty list for ext_modules that
# tests as truthful - this causes the package to be treated as non-pure on all
# relevant setuptools versions.
class ExtModules(list):
    def __bool__(self):
        return not pure


from setuptools import setup  # noqa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import versioneer  # noqa

del sys.path[0]

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
import debugpy
import debugpy._vendored

del sys.path[0]


PYDEVD_ROOT = debugpy._vendored.project_root("pydevd")
DEBUGBY_ROOT = os.path.dirname(os.path.abspath(debugpy.__file__))


def get_buildplatform():
    if "-p" in sys.argv:
        return sys.argv[sys.argv.index("-p") + 1]
    return None


def cython_build():
    print("Compiling extension modules (set SKIP_CYTHON_BUILD=1 to omit)")
    subprocess.call(
        [
            sys.executable,
            os.path.join(PYDEVD_ROOT, "setup_cython.py"),
            "build_ext",
            "-i",
        ]
    )


def iter_vendored_files():
    # Add pydevd files as data files for this package. They are not
    # treated as a package of their own, because we don't actually
    # want to provide pydevd - just use our own copy internally.
    for project in debugpy._vendored.list_all():
        for filename in debugpy._vendored.iter_packaging_files(project):
            yield filename


with open("DESCRIPTION.md", "r") as fh:
    long_description = fh.read()


if __name__ == "__main__":
    if not os.getenv("SKIP_CYTHON_BUILD"):
        cython_build()

    extras = {}
    platforms = get_buildplatform()
    if platforms is not None:
        extras["platforms"] = platforms

    setup(
        name="debugpy",
        version=versioneer.get_version(),
        description="An implementation of the Debug Adapter Protocol for Python",  # noqa
        long_description=long_description,
        long_description_content_type="text/markdown",
        license="MIT",
        author="Microsoft Corporation",
        author_email="ptvshelp@microsoft.com",
        url="https://aka.ms/debugpy",
        python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*",
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.5",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Topic :: Software Development :: Debuggers",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: MacOS",
            "Operating System :: POSIX",
            "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
            "License :: OSI Approved :: MIT License",
        ],
        package_dir={"": "src"},
        packages=[
            "debugpy",
            "debugpy.adapter",
            "debugpy.common",
            "debugpy.launcher",
            "debugpy.server",
            "debugpy._vendored",
        ],
        package_data={
            "debugpy": ["ThirdPartyNotices.txt"],
            "debugpy._vendored": list(iter_vendored_files()),
        },
        ext_modules=ExtModules(),
        has_ext_modules=lambda: not pure,
        cmdclass=versioneer.get_cmdclass(),
        **extras
    )
