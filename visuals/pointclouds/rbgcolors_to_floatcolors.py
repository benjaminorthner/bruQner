"""
.pts cloud files from polycam have an int format (0-255) for their RGB values. 
The .tox file i use in Touchdesigner for pointcloud sorting expects floats. Hence this converts the .pts (op .xyz)
files to that format
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import gzip

# === Configure this: point INPUT_PATH to your file (txt or .gz) ===
INPUT_PATH = Path(r"TSOE_Setup_pointcloud.pts") 

# === Formatting ===
DECIMALS = 6  # decimal places for Scalar_field, Rf, Gf, Bf

def derive_output_path(inp: Path, suffix="_floatcolors"):
    """
    Insert suffix before the final non-.gz extension.
    Examples:
      points.txt        -> points_floatcolors.txt
      points.xyzrgb.txt -> points.xyzrgb_floatcolors.txt
      points.txt.gz     -> points_floatcolors.txt.gz
    """
    if inp.suffix == ".gz":
        base = inp.with_suffix("")  # remove .gz
        # Rebuild name without using Path.with_stem (better compatibility)
        new_name = f"{base.stem}{suffix}{base.suffix}.gz"
        return base.with_name(new_name)
    else:
        return inp.with_name(f"{inp.stem}{suffix}{inp.suffix}")

def open_read(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline=None)
    return open(path, "rt", encoding="utf-8", newline=None)

def open_write(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "wt", encoding="utf-8", newline="\n")
    return open(path, "wt", encoding="utf-8", newline="\n")

def process_file(inp: Path, outp: Path, decimals: int = 6):
    scale = 255.0
    fmt = f"{{:.{decimals}f}}"

    with open_read(inp) as fin, open_write(outp) as fout:
        # Header row
        fout.write("X Y Z Scalar_field Rf Gf Bf\n")

        for line in fin:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 7:
                continue  # require x y z s r g b

            # Preserve XYZ as-is (no reformat to avoid FP drift/verbosity)
            x, y, z = parts[0], parts[1], parts[2]

            try:
                s = float(parts[3]) / scale     # scalar field scaled to [0,1]
                r = int(parts[4]) / scale       # colors scaled to [0,1]
                g = int(parts[5]) / scale
                b = int(parts[6]) / scale
            except ValueError:
                continue  # skip malformed numeric rows

            fout.write(
                f"{x} {y} {z} {fmt.format(s)} {fmt.format(r)} {fmt.format(g)} {fmt.format(b)}\n"
            )

if __name__ == "__main__":
    OUTPUT_PATH = derive_output_path(INPUT_PATH)
    process_file(INPUT_PATH, OUTPUT_PATH, DECIMALS)
    print(f"Done. Wrote: {OUTPUT_PATH}")