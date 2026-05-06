import subprocess
import json
import sys
import os


def run_check(name, cmd):
    """Runs a command and returns a structured result."""
    print(f"Running {name}...")
    proc = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    # Special case for pytest: "no tests ran" is not a failure
    if name == "Tests (Pytest)" and "no tests ran" in proc.stdout:
        return {
            "tool": name,
            "success": True,
            "output": "Passed (no tests found)",
            "error": proc.stderr
        }
    return {
        "tool": name,
        "success": proc.returncode == 0,
        "output": proc.stdout if proc.returncode != 0 else "Passed",
        "error": proc.stderr
    }


def check_json_files():
    """Check all JSON files for valid syntax."""
    print("Checking JSON files...")
    json_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and common build/cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'dist', 'build']]
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    errors = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{json_file}: {str(e)}")
        except Exception as e:
            errors.append(f"{json_file}: {str(e)}")
    
    if errors:
        return {
            "tool": "JSON Syntax Check",
            "success": False,
            "output": "\\n".join(errors),
            "error": ""
        }
    else:
        return {
            "tool": "JSON Syntax Check",
            "success": True,
            "output": f"Passed ({len(json_files)} files checked)",
            "error": ""
        }


def main():
    # 1. Ruff: Linting & Formatting (2026 Standard)
    # Using --output-format json as per v0.15+ docs
    checks = [
        run_check("Linter (Ruff)", "ruff check --output-format json ."),
        run_check("Formatter (Ruff)", "ruff format --check ."),
        check_json_files(),  # Add JSON syntax check
    ]

    # 2. Mypy: Type Checking (v1.20)
    checks.append(run_check("Types (Mypy)", "mypy --no-error-summary ."))

    # 3. Bandit: Security
    checks.append(run_check("Security (Bandit)", "bandit -r . -f json -q"))

    # 4. Pytest: Execution
    # Requires pytest-json-report installed
    checks.append(run_check("Tests (Pytest)", "pytest --json-report --json-report-file=.report.json --quiet"))

    # Summary Generation
    failed = [c for c in checks if not c["success"]]
    
    if not failed:
        print("\n✅ ALL CHECKS PASSED. READY FOR PR.")
        sys.exit(0)
    else:
        print("\n❌ CHECKS FAILED. See summary below:")
        print(json.dumps(failed, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()