# Disc-Recovery-Organizer

This script is meant to be executed in **Python after using [PhotoRec](https://www.cgsecurity.org/wiki/PhotoRec)** disk recovery software.
It helps organize, clean, and post-process the chaotic output generated inside `recup_dir.*` folders. The code was made based on the output of 7.3-WIP but it should work normally in other versions.

The goal is to reduce manual work after recovery by sorting files, removing obvious junk (like thumbnails), and preparing the data for further analysis such as duplicate detection.

## Context

PhotoRec is excellent at recovering files, but it does not preserve filenames, folder structure, or metadata relationships. The result is usually thousands of files spread across multiple `recup_dir.*` folders.

This tool was created to operate **after recovery is finished**, not during, and assumes that:

- PhotoRec already completed successfully
- Files are located inside `recup_dir.*` folders
- You want a structured and readable output

## Features

• Organizes recovered files into a single `organized` folder
• Lets you choose where the `organized` folder will be created
• Sorts files by type and content
• Detects large videos (≥ 1 GB) and isolates them
• Separates images with and without EXIF metadata
• Groups images by camera model when available
• Deletes small images likely to be thumbnails
• Cleans all files inside `recup_dir.*` folders (destructive, optional)
• Provides a summary with counters after organization
• Colored terminal output for better readability

## Organization Rules

Recovered files are moved according to these rules:

Large videos
Moved to:

```
organized/large_videos_1gb_plus/
```

Images with EXIF metadata
Moved to:

```
organized/images_with_metadata/<camera_model>/
```

Images without metadata
Moved to:

```
organized/images_without_metadata/
```

Other supported media types (audio, archives, small videos)
Moved to:

```
organized/<extension>/
```

Unsupported file types are ignored.

## Thumbnail Cleanup

The script can delete images below a configurable resolution threshold.
This is intended to remove:

• Thumbnails
• Preview images
• UI assets
• Cached miniatures

The scan includes:

• All `recup_dir.*` folders
• The `organized` folder and all its subfolders

Deletion is permanent and requires confirmation.

## Requirements

• Python 3.9+ recommended
• Pillow (PIL fork)

Install dependencies with:

```
pip install pillow
```

On Windows, ANSI colors work out of the box in modern terminals.
The folder picker uses `tkinter`, which is included with standard Python installs.

## Usage

1. Run PhotoRec and finish the recovery process
2. Place this script in the directory containing `recup_dir.*`
3. Run the script:

```
python organizer.py
```

4. Choose where the `organized` folder should be created
5. Use the menu to organize, clean thumbnails, or clean recovery folders

## Safety Notes

• File deletion is permanent
• Cleaning `recup_dir.*` removes all remaining recovered files
• Always review the organized output before deleting anything
• It is recommended to keep backups until you verify the results

## Intended Workflow

PhotoRec recovery
→ Organization with this script
→ Optional thumbnail cleanup
→ Optional duplicate detection (external tool or future script)

This script intentionally does **not** attempt deduplication, to keep responsibilities clear and avoid accidental data loss.

For that i do recommend using specialized tools like [dupeGuru](https://dupeguru.voltaicideas.net/).