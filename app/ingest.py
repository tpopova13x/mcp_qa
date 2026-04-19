import sys

from user_documentation.ingest import ingest_user_docu
from internal_documentation.ingest import ingest_internal_docu
from existing_tests.ingest import ingest_tests


COMMANDS = {
    "user-docu": ingest_user_docu,
    "internal-docu": ingest_internal_docu,
    "tests": ingest_tests,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python ingest.py <{'|'.join(COMMANDS)}>")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
