"""Automated File Organizer & Cleanup Utility

Sorts files in a folder (e.g. Downloads) into category subfolders
(Documents, Images, Videos, Archives, Code, Others) based on file extension.

Concepts used: os.scandir, shutil.move, pathlib, dictionaries,
try-except (FileExistsError, PermissionError), logging.

Run with:  python organizer.py
"""

import logging
import os
import shutil
from pathlib import Path

# Extension -> category folder
EXTENSION_MAP = {
    # Documents
    ".pdf": "Documents", ".doc": "Documents", ".docx": "Documents",
    ".txt": "Documents", ".xls": "Documents", ".xlsx": "Documents",
    ".ppt": "Documents", ".pptx": "Documents", ".csv": "Documents",
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".webp": "Images", ".svg": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos",
    ".mov": "Videos", ".wmv": "Videos",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives",
    ".tar": "Archives", ".gz": "Archives",
    # Code
    ".py": "Code", ".js": "Code", ".html": "Code", ".css": "Code",
    ".java": "Code", ".c": "Code", ".cpp": "Code", ".json": "Code",
}

DEFAULT_CATEGORY = "Others"
SKIP_EXTENSIONS = {".tmp", ".crdownload", ".part"}  # unfinished downloads
LOG_FILE = "organizer.log"

# Logging goes to BOTH the console and organizer.log
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def get_category(filename):
    """Return the category folder name for a file based on its extension."""
    ext = Path(filename).suffix.lower()
    return EXTENSION_MAP.get(ext, DEFAULT_CATEGORY)


def unique_destination(dest_folder, filename):
    """Handle naming collisions: report.pdf -> report_1.pdf -> report_2.pdf ..."""
    destination = Path(dest_folder) / filename
    stem, suffix = destination.stem, destination.suffix
    counter = 1
    while destination.exists():
        destination = Path(dest_folder) / f"{stem}_{counter}{suffix}"
        counter += 1
    return destination


def organize_folder(folder, dry_run=False):
    """Move every file in `folder` into its category subfolder.

    Returns a dict with counts: moved per category, skipped, errors.
    """
    summary = {"moved": {}, "skipped": 0, "errors": 0}
    script_name = Path(__file__).name

    # Collect files first so we don't scan while moving
    with os.scandir(folder) as entries:
        files = [e for e in entries if e.is_file()]

    for entry in files:
        name = entry.name
        ext = Path(name).suffix.lower()

        # Skip this script, the log file, hidden files and unfinished downloads
        if name in (script_name, LOG_FILE) or name.startswith(".") or ext in SKIP_EXTENSIONS:
            logging.info("Skipped: %s", name)
            summary["skipped"] += 1
            continue

        category = get_category(name)
        dest_folder = Path(folder) / category

        try:
            if not dry_run:
                dest_folder.mkdir(exist_ok=True)           # create subfolder dynamically
            destination = unique_destination(dest_folder, name)

            if dry_run:
                logging.info("[DRY RUN] %s -> %s/%s", name, category, destination.name)
            else:
                shutil.move(entry.path, str(destination))
                logging.info("Moved: %s -> %s/%s", name, category, destination.name)

            summary["moved"][category] = summary["moved"].get(category, 0) + 1

        except PermissionError:
            logging.error("Permission denied (file may be open/locked): %s", name)
            summary["errors"] += 1
        except FileExistsError:
            logging.error("File already exists, could not move: %s", name)
            summary["errors"] += 1
        except OSError as exc:
            logging.error("Could not move %s: %s", name, exc)
            summary["errors"] += 1

    return summary


def print_summary(summary, dry_run):
    total = sum(summary["moved"].values())
    print("\n" + "=" * 40)
    print("   EXECUTION SUMMARY" + ("  (DRY RUN)" if dry_run else ""))
    print("=" * 40)
    for category, count in sorted(summary["moved"].items()):
        print(f"  {category:<12} : {count} file(s)")
    print("-" * 40)
    print(f"  Total {'to move' if dry_run else 'files relocated'} : {total}")
    print(f"  Skipped              : {summary['skipped']}")
    print(f"  Errors               : {summary['errors']}")
    print("=" * 40)
    print(f"  Log saved to: {LOG_FILE}\n")


def main():
    default_folder = Path.home() / "Downloads"
    print("=== FILE ORGANIZER ===")
    user_input = input(f"Folder to organize [{default_folder}]: ").strip().strip('"')
    folder = Path(user_input) if user_input else default_folder

    if not folder.is_dir():
        print(f"Error: '{folder}' is not a valid folder.")
        return

    mode = input("Do a dry run first (preview only, nothing moves)? (y/n) [y]: ").strip().lower()
    dry_run = mode != "n"

    if not dry_run:
        confirm = input(f"This will MOVE files inside '{folder}'. Continue? (y/n): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return

    summary = organize_folder(folder, dry_run=dry_run)
    print_summary(summary, dry_run)


if __name__ == "__main__":
    main()
