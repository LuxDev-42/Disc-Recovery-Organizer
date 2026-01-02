import os
import shutil
import tkinter as tk
from tkinter import filedialog
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS

# ======== LOGGING / COLORS ========

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def log(tag, message, color=C.RESET):
    print(f"{color}[{tag}]{C.RESET} {message}")

# ============ CONSTANTS ============
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".3gp", ".mpg", ".mpeg"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tiff"}
AUDIO_EXT = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".amr"}
ARCHIVE_EXT = {".zip", ".rar"}
MEDIA_EXT = VIDEO_EXT | IMAGE_EXT | AUDIO_EXT | ARCHIVE_EXT

SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1 GB
base_dir = os.getcwd()
SELF_NAME = os.path.basename(__file__)

# ============ GLOBALS ============
total_moved = 0
by_extension = defaultdict(int)
by_model = defaultdict(int)
images_no_metadata = 0
max_width = 400
max_height = 400

# ======== WELCOME MESSAGE ========

def print_welcome():

    print(C.BOLD + "=" * 60 + C.RESET)
    print(C.BOLD + " PhotoRec Recovery Organizer & Cleanup Utility" + C.RESET)
    print(C.BOLD + "=" * 60 + C.RESET)
    print()
    print("This tool is designed to be used AFTER running PhotoRec.")
    print("It helps organize recovered files, clean recup_dir folders,")
    print("and remove small images that are likely thumbnails.")
    print()
    print(C.YELLOW + "Use carefully. Deletions are permanent." + C.RESET)
    print()

# ===== DESTINATION SELECTION =====

def select_destination_dir(base_dir):
    log("INFO", "Select where the files will be organized.", C.CYAN)
    choice = input(
        "Use the current script folder as destination? (y/n): "
    ).strip().lower()

    if choice == "y":
        dest_base = base_dir
    else:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        selected = filedialog.askdirectory(
            title="Select destination folder for organized files"
        )

        root.destroy()

        if not selected:
            log("INFO", "No folder selected. Using current script folder.", C.CYAN)
            dest_base = base_dir
        else:
            dest_base = os.path.abspath(selected)

    # safety check: avoid organizing inside recup_dir.*
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if entry.lower().startswith("recup_dir.") and dest_base.startswith(entry_path):
            raise RuntimeError(
                "Destination cannot be inside a recup_dir.* folder."
            )

    organized_path = os.path.join(dest_base, "organized")
    os.makedirs(organized_path, exist_ok=True)

    log("INFO", f"Organized files will be stored in:\n{organized_path}\n", C.GREEN)
    return organized_path

# ======== FILE OPERATIONS ========
def safe_move(src, dst_dir):
    global total_moved
    os.makedirs(dst_dir, exist_ok=True)
    name = os.path.basename(src)
    dst = os.path.join(dst_dir, name)
    base, ext = os.path.splitext(name)
    counter = 1
    while os.path.exists(dst):
        dst = os.path.join(dst_dir, f"{base}_{counter}{ext}")
        counter += 1
    shutil.move(src, dst)
    total_moved += 1

def get_camera_model(image_path):
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()
            if not exif:
                return None
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "Model" and isinstance(value, str):
                    return value.strip()
    except Exception:
        pass
    return None

# ====== CLEANUP OPERATIONS =======
def clean_recup_dirs(base_dir):
    for entry in os.listdir(base_dir):
        entry_path = os.path.join(base_dir, entry)
        if not os.path.isdir(entry_path) or not entry.lower().startswith("recup_dir."):
            continue
        for root, _, files in os.walk(entry_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    log("DELETE", file_path, C.RED)
                except Exception as e:
                    log("FAIL", f"{file_path}: {e}", C.RED)

def delete_small_images(base_dir, organized_dir, max_w, max_h):

    log("INFO", "Starting cleanup...", C.CYAN)
    deleted = 0
    scan_roots = [os.path.join(base_dir, entry) for entry in os.listdir(base_dir)
                  if os.path.isdir(os.path.join(base_dir, entry)) and entry.lower().startswith("recup_dir.")]
    
    if os.path.isdir(organized_dir):
        scan_roots.append(organized_dir)

    for root_dir in scan_roots:
        for root, _, files in os.walk(root_dir):
            for file in files:
                ext = os.path.splitext(file.lower())[1]
                if ext not in IMAGE_EXT:
                    continue
                file_path = os.path.join(root, file)
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                    if width < max_w and height < max_h:
                        os.remove(file_path)
                        deleted += 1
                        log("DELETE", f"thumbnail {width}x{height} -> {file_path}", C.RED)
                except Exception:
                    continue
    log("INFO", f"thumbnail cleanup completed, deleted {deleted} images", C.GREEN)

# ========= ORGANIZATION ==========
def organize(organized_dir):

    global total_moved, by_extension, by_model, images_no_metadata

    total_moved = 0
    by_extension.clear()
    by_model.clear()
    images_no_metadata = 0

    large_videos_dir = os.path.join(organized_dir, "large_videos_1gb_plus")
    images_with_meta = os.path.join(organized_dir, "images_with_metadata")
    images_without_meta = os.path.join(organized_dir, "images_without_metadata")
    os.makedirs(organized_dir, exist_ok=True)

    for item in os.listdir(base_dir):
        if not item.lower().startswith("recup_dir."):
            continue
        recup_path = os.path.join(base_dir, item)
        log("SCAN", f"processing folder: {item}", C.CYAN)
        for dirpath, _, filenames in os.walk(recup_path):
            for filename in filenames:
                if filename == SELF_NAME:
                    continue
                file_path = os.path.join(dirpath, filename)
                ext = os.path.splitext(filename.lower())[1]
                if ext not in MEDIA_EXT:
                    continue
                
                if ext in VIDEO_EXT and os.path.getsize(file_path) >= SIZE_LIMIT:
                    safe_move(file_path, large_videos_dir)
                    by_extension[ext[1:]] += 1
                    log("MOVE", f"large video -> {filename}", C.GREEN)
                elif ext in IMAGE_EXT:
                    model = get_camera_model(file_path)
                    if model:
                        safe_move(file_path, os.path.join(images_with_meta, model))
                        by_model[model] += 1
                        log("MOVE", f"image with metadata ({model}) -> {filename}", C.GREEN)
                    else:
                        safe_move(file_path, images_without_meta)
                        images_no_metadata += 1
                        log("MOVE", f"image without metadata -> {filename}", C.GREEN)
                else:
                    ext_dir = os.path.join(organized_dir, ext[1:])
                    safe_move(file_path, ext_dir)
                    by_extension[ext[1:]] += 1
                    log("MOVE", f"by extension ({ext[1:]}) -> {filename}", C.GREEN)

def print_summary():
    print("\n========== SUMMARY ==========")
    print(f"organized files: {total_moved}")
    if by_extension:
        print("\nby extension:")
        for ext, count in sorted(by_extension.items()):
            print(f"{ext}: {count}")
    if by_model:
        print("\nby camera model:")
        for model, count in sorted(by_model.items()):
            print(f"{model}: {count}")
    if images_no_metadata:
        print(f"\nno metadata: {images_no_metadata} files")
    print("=============================\n")

# ============= MENU ==============
def organizer_menu(base_dir, organized_dir):

    global max_width, max_height

    while True:
        print("\nSelect an option:")
        print("1 - Organize recovery files")
        print("2 - Delete thumbnail images (small resolution)")
        print(f"3 - Change thumbnail size (current: {max_width}x{max_height})")
        print("4 - Clean all files inside recup_dir.*")
        print("5 - Help")
        print("0 - Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            if input("This will move files into the organized folder. Continue? (y/n): ").strip().lower() == "y":
                organize(organized_dir)
                log("INFO", "organize operation completed", C.GREEN)
                print_summary()
            else:
                log("INFO", "operation cancelled", C.YELLOW)
        elif choice == "2":
            if input("This will DELETE small images. Continue? (y/n): ").strip().lower() == "y":
                delete_small_images(base_dir, organized_dir, max_width, max_height)
            else:
                log("INFO", "operation cancelled", C.YELLOW)
        elif choice == "3":
            try:
                max_width = int(input("Enter new maximum width: ").strip())
                max_height = int(input("Enter new maximum height: ").strip())
                log("INFO", f"Thumbnail size updated to {max_width}x{max_height}.", C.GREEN)
            except ValueError:
                log("ERROR", "Invalid input. Please enter integers.", C.RED)
        elif choice == "4":
            if input("This will DELETE ALL FILES inside recup_dir.*. Are you sure? (y/n): ").strip().lower() == "y":
                clean_recup_dirs(base_dir)
                log("INFO", "clean operation completed", C.GREEN)
            else:
                log("INFO", "operation cancelled", C.YELLOW)
        elif choice == "5":
            print("\n========== HELP ==========")
            print("1 - Organize recovery files")
            print("    Scans recup_dir.* folders and sorts files by type:")
            print("    • Large videos (≥1GB) → large_videos_1gb_plus/")
            print("    • Images with metadata → images_with_metadata/{camera_model}/")
            print("    • Images without metadata → images_without_metadata/")
            print("    • Other media → organized/{extension}/")
            print("\n2 - Delete thumbnail images")
            print("    Removes small images smaller than the set dimensions.")
            print(f"    Current threshold: {max_width}x{max_height}")
            print("\n3 - Change thumbnail size")
            print("    Set new width and height for thumbnail deletion.")
            print("\n4 - Clean recup_dir.* folders")
            print("    Permanently deletes ALL files in recup_dir.* folders.")
            print("    ⚠️  WARNING: This cannot be undone!")
            print("===========================\n")
        elif choice == "0":
            break
        else:
            log("ERROR", "invalid option", C.RED)

# ============== MAIN =============

if __name__ == "__main__":
    print_welcome()
    try:
        ORGANIZED_DIR = select_destination_dir(base_dir)
    except RuntimeError as e:
        log("ERROR", str(e), C.RED)
        exit(1)

    organizer_menu(base_dir, ORGANIZED_DIR)
