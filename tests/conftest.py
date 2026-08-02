"""Keep framework test execution from creating repository bytecode debris."""

import sys


sys.dont_write_bytecode = True
