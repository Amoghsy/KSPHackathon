import shutil
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
BUILD_DIR = BASE_DIR / "build"


def main():
    print("=" * 60)
    print("Building SCRB Backend for Zoho Catalyst AppSail")
    print("Target: Linux x86_64 / Python 3.12")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Remove previous build
    # ---------------------------------------------------------

    if BUILD_DIR.exists():
        print("\n[1/4] Removing previous build...")

        shutil.rmtree(BUILD_DIR)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 2. Install Linux-compatible dependencies
    # ---------------------------------------------------------

    requirements = BASE_DIR / "requirements.txt"

    if not requirements.exists():
        raise FileNotFoundError(
            f"requirements.txt not found: {requirements}"
        )

    print("\n[2/4] Installing Linux Python 3.12 dependencies...")

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",

            "-r",
            str(requirements),

            "--target",
            str(BUILD_DIR),

            # Catalyst runtime target
            "--platform",
            "manylinux2014_x86_64",

            "--python-version",
            "3.12",

            "--implementation",
            "cp",

            # Required when cross-installing platform-specific wheels
            "--only-binary=:all:",

            "--upgrade",
        ]
    )

    # ---------------------------------------------------------
    # 3. Copy FastAPI source
    # ---------------------------------------------------------

    print("\n[3/4] Copying FastAPI application...")

    source_app = BASE_DIR / "app"
    destination_app = BUILD_DIR / "app"

    if not source_app.exists():
        raise FileNotFoundError(
            f"Application directory not found: {source_app}"
        )

    shutil.copytree(
        source_app,
        destination_app,
        dirs_exist_ok=True,
    )

    # Copy startup file

    startup_file = BASE_DIR / "app_start.py"

    if not startup_file.exists():
        raise FileNotFoundError(
            f"app_start.py not found: {startup_file}"
        )

    shutil.copy2(
        startup_file,
        BUILD_DIR / "app_start.py",
    )

    # ---------------------------------------------------------
    # 4. Finish
    # ---------------------------------------------------------

    print("\n[4/4] Build completed.")

    print("\n" + "=" * 60)
    print("APPSAIL BUILD SUCCESSFUL")
    print("=" * 60)

    print(f"\nBuild directory:\n{BUILD_DIR}")

    print(
        "\nIMPORTANT:"
        "\nThis build contains Linux binaries."
        "\nDo not run this build directly with Windows Python."
    )


if __name__ == "__main__":
    main()