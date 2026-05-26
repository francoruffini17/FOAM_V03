import os
import shutil

# ─────────────────────────────────────────
#  USER PARAMETERS  ← edit these
# ─────────────────────────────────────────
VIDEO_AAA   = 2006    # which Video folder  (e.g. 30 → Video_030)
SIM_START   = 3000         # first SIM number to extract
SIM_END     = 3008        # last  SIM number to extract (inclusive)
# ─────────────────────────────────────────

BASE_DIR    = "I002_Videos"
OUTPUT_DIR  = os.path.join(BASE_DIR, "Video_extract")

def pad(n):
    """Return a 3-digit zero-padded string."""
    return str(n).zfill(3)

def main():
    # Create output folder if needed
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output folder: {OUTPUT_DIR}\n")

    copied  = 0
    missing = 0

    for xxx in range(SIM_START, SIM_END + 1):
        aaa_str = pad(VIDEO_AAA)
        xxx_str = pad(xxx)

        src_file = os.path.join(
            BASE_DIR,
            f"Video_{aaa_str}",
            f"SIM_{xxx_str}",
            f"video_test_SIM_{xxx_str}.mp4"
        )

        dst_file = os.path.join(
            OUTPUT_DIR,
            f"Video_{aaa_str}_SIM_{xxx_str}.mp4"
        )

        if os.path.isfile(src_file):
            shutil.copy2(src_file, dst_file)
            print(f"  ✔  Copied: {src_file}  →  {dst_file}")
            copied += 1
        else:
            print(f"  ⚠  WARNING: File not found, skipping: {src_file}")
            missing += 1

    print(f"\nDone. {copied} file(s) copied, {missing} file(s) not found.")

if __name__ == "__main__":
    main()