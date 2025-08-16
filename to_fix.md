
(.venv) G:\projects\pr-analyzer>ruff check --unsafe-fixes .
src\project_analyzer\cli\args.py:73:151: E501 Line too long (172 > 150)
   |
71 | …
72 | …
73 | …de.md", default=None, help="Generate a summary file (default: claude.md).")
   |                                                       ^^^^^^^^^^^^^^^^^^^^^^ E501
74 | …
75 | …
   |

src\project_analyzer\core\scanner.py:22:31: F821 Undefined name `original_dirs`
   |
21 |     for root, dirs, files in os.walk(project_path, topdown=True):
22 |         dirs[:] = [d for d in original_dirs]
   |                               ^^^^^^^^^^^^^ F821
23 |
24 |         for file in files:
   |

src\project_analyzer\core\scanner.py:32:151: E501 Line too long (151 > 150)
   |
31 | …
32 | …asename(rel_path_norm), pattern) for pattern in allow_patterns):
   |                                                                 ^ E501
33 | …
   |

Found 3 errors.

(.venv) G:\projects\pr-analyzer>ruff check --unsafe-fixes .
src\project_analyzer\core\scanner.py:22:31: F821 Undefined name `original_dirs`
   |
21 |     for root, dirs, files in os.walk(project_path, topdown=True):
22 |         dirs[:] = [d for d in original_dirs]
   |                               ^^^^^^^^^^^^^ F821
23 |
24 |         for file in files:
   |

Found 1 error.