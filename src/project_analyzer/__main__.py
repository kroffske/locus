"""
Enables running the project analyzer as a module with `python -m project_analyzer`.
"""
import sys
from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
