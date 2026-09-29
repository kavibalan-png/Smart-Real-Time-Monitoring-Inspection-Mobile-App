"""Run tests and write results to file."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/test_intelligence.py", 
     "tests/test_security.py", 
     "-v", "--tb=short", "--no-header"],
    capture_output=True,
    text=True,
    cwd="."
)

with open("test_results.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nReturn code: {result.returncode}")

print("Tests complete. Return code:", result.returncode)
print(result.stdout[-3000:] if len(result.stdout) > 3000 else result.stdout)
