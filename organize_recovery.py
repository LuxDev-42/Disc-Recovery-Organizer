import os
import shutil
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS

# ============ CONSTANTS ============
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".3gp", ".mpg", ".mpeg"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp", ".bmp", ".tiff"}
AUDIO_EXT = {".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".amr"}
ARCHIVE_EXT = {".zip", ".rar"}
MEDIA_EXT = VIDEO_EXT | IMAGE_EXT | AUDIO_EXT | ARCHIVE_EXT

SIZE_LIMIT = 1 * 1024 * 1024 * 1024  # 1 GB
BASE_DIR = os.getcwd()
ORGANIZED_DIR = os.path.join(BASE_DIR, "organized")
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
    print("=" * 60)
    print(" PhotoRec Recovery Organizer & Cleanup Utility")
    print("=" * 60)
    print()
    print("This tool is designed to be used AFTER running PhotoRec.")
    print("It helps organize recovered files, clean recup_dir folders,")
    print("and remove small images that are likely thumbnails.")
    print()
    print("Make sure PhotoRec has already finished recovering files,")
    print("and that you have proper read/write permissions.")
    print()
    print("Use carefully. Deletions are permanent.")
    print()


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
                    print(f"[DELETE] {file_path}")
                except Exception as e:
                    print(f"[FAIL] {file_path}: {e}")

def delete_small_images(base_dir, max_w, max_h):
    print("\nStarting cleanup...")
    deleted = 0
    scan_roots = [os.path.join(base_dir, entry) for entry in os.listdir(base_dir)
                  if os.path.isdir(os.path.join(base_dir, entry)) and entry.lower().startswith("recup_dir.")]
    
    organized_path = os.path.join(base_dir, "organized")
    if os.path.isdir(organized_path):
        scan_roots.append(organized_path)

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
                        print(f"[DELETE] thumbnail {width}x{height} -> {file_path}")
                except Exception:
                    continue
    print(f"\nthumbnail cleanup completed, deleted {deleted} images")

# ========= ORGANIZATION ==========
def organize():
    global images_no_metadata
    large_videos_dir = os.path.join(ORGANIZED_DIR, "large_videos_1gb_plus")
    images_with_meta = os.path.join(ORGANIZED_DIR, "images_with_metadata")
    images_without_meta = os.path.join(ORGANIZED_DIR, "images_without_metadata")
    os.makedirs(ORGANIZED_DIR, exist_ok=True)

    for item in os.listdir(BASE_DIR):
        if not item.lower().startswith("recup_dir."):
            continue
        recup_path = os.path.join(BASE_DIR, item)
        print(f"\n[SCAN] processing folder: {item}")
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
                    print(f"[MOVE] large video -> {filename}")
                elif ext in IMAGE_EXT:
                    model = get_camera_model(file_path)
                    if model:
                        safe_move(file_path, os.path.join(images_with_meta, model))
                        by_model[model] += 1
                        print(f"[MOVE] image with metadata ({model}) -> {filename}")
                    else:
                        safe_move(file_path, images_without_meta)
                        images_no_metadata += 1
                        print(f"[MOVE] image without metadata -> {filename}")
                else:
                    ext_dir = os.path.join(ORGANIZED_DIR, ext[1:])
                    safe_move(file_path, ext_dir)
                    by_extension[ext[1:]] += 1
                    print(f"[MOVE] by extension ({ext[1:]}) -> {filename}")

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
def organizer_menu(base_dir):
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
                organize()
                print("organize operation completed")
                print_summary()
            else:
                print("operation cancelled")
        elif choice == "2":
            if input("This will DELETE small images. Continue? (y/n): ").strip().lower() == "y":
                delete_small_images(base_dir, max_width, max_height)
            else:
                print("operation cancelled")
        elif choice == "3":
            try:
                max_width = int(input("Enter new maximum width: ").strip())
                max_height = int(input("Enter new maximum height: ").strip())
                print(f"Thumbnail size updated to {max_width}x{max_height}.")
            except ValueError:
                print("Invalid input. Please enter integers.")
        elif choice == "4":
            if input("This will DELETE ALL FILES inside recup_dir.*. Are you sure? (y/n): ").strip().lower() == "y":
                clean_recup_dirs(base_dir)
                print("clean operation completed")
            else:
                print("operation cancelled")
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
            print("invalid option")

# ============== MAIN =============
if __name__ == "__main__":
    print_welcome()
    organizer_menu(os.getcwd())
