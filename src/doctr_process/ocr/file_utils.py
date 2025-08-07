import logging
import os
import zipfile


def zip_folder(folder_path: str, output_zip_path: str) -> None:
    """Zip the contents of *folder_path* into *output_zip_path*.

    Existing archives are overwritten. Subdirectories are included
    recursively with relative paths preserved."""
    if not os.path.isdir(folder_path):
        logging.warning(f"Folder not found for zipping: {folder_path}")
        return

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, start=folder_path)
                zf.write(abs_path, rel_path)

    logging.info(f"Zipped valid pages: {output_zip_path}")
