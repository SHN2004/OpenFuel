import os
import sys

required_files = [
    ".github/workflows",
    "src/__init__.py",
    "src/scraper.py",
    "src/utils.py",
    "tests/__init__.py",
    "tests/test_scraper.py",
    "tests/conftest.py",
    ".gitignore",
    ".python-version",
    "README.md",
    "requirements.txt",
    "prices.json"
]

missing = []
for f in required_files:
    if not os.path.exists(f):
        missing.append(f)

if missing:
    print(f"Missing files: {missing}")
    sys.exit(1)

# Verify .gitignore content
with open(".gitignore", "r") as f:
    content = f.read()
    # Check for the specific comment block
    if "# OpenFuel - Explicitly TRACK prices.json (The DB)" not in content:
         print("Error: Explicit comment missing in .gitignore")
         sys.exit(1)

# Verify prices.json
with open("prices.json", "r") as f:
    if f.read().strip() != "{}":
        print("prices.json is not empty object")
        sys.exit(1)

print("Verification passed!")
