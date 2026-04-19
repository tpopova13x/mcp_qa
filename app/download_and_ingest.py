import sys

from user_documentation.download import fetch_files_from_gitlab
from user_documentation.ingest import ingest_user_docu
from internal_documentation.download import fetch_pages_from_confluence
from internal_documentation.ingest import ingest_internal_docu
from existing_tests.download import export_xray_tests_to_csv
from existing_tests.ingest import ingest_tests


def download_and_ingest_user_docu():
    fetch_files_from_gitlab()
    ingest_user_docu()


def download_and_ingest_internal_docu():
    fetch_pages_from_confluence()
    ingest_internal_docu()


def download_and_ingest_tests():
    export_xray_tests_to_csv()
    ingest_tests()


COMMANDS = {
    "user-docu": download_and_ingest_user_docu,
    "internal-docu": download_and_ingest_internal_docu,
    "tests": download_and_ingest_tests,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python download_and_ingest.py <{'|'.join(COMMANDS)}>")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
