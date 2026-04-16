import glob
import os
import sys
import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.bibliography import BibliographyManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse content from TeX and Bib files.")
    parser.add_argument('-t', '--tex', type=str, help='Path to the target .tex file')
    parser.add_argument('-b', '--bib', type=str, help='Path to the target .bib file')
    args = parser.parse_args()

    # Parse the file path and apply fallback logic
    bib_path = args.bib
    if not bib_path:
        bib_files = glob.glob('*.bib')
        if bib_files:
            bib_path = bib_files[0]
        else:
            sys.exit("Error: No .bib file specified via -b/--bib, and no default .bib file found in the current directory.")

    tex_path = args.tex
    if not tex_path:
        tex_files = glob.glob('*.tex')
        if tex_files:
            tex_path = tex_files[0]
        else:
            tex_path = None
    
    print(f"Using BIB file: {bib_path}")
    if tex_path:
        print(f"Using TEX file: {tex_path}")

    # ===== Main Process =====
    manager = BibliographyManager()
    
    # 1. Extract
    manager.load_references(bib_path)
    if tex_path:
        manager.load_main_text(tex_path)
    # 2. Format
    manager.format_all()
    # 3. Deduplicate
    manager.deduplicate()
    # 4. Sort
    manager.sort()
    # 5. Remove Uncited
    if tex_path:
        manager.remove_uncited()
    # 6. Save
    if manager.get_bibnumber() > 0:
      save_path = manager.save_to_file()
      print("Task Completed Successfully!")
      print(f"Output saved to: {os.path.abspath(save_path)}")
