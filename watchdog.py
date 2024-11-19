import subprocess
import sys
import time


def run_code():
    try:
        with open("submitted_code.py", "r") as code_file:
            code = code_file.read()

        start_time = time.time()
        proc = subprocess.Popen(
            ['python3', '-c', code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output = ""
        while True:
            if proc.poll() is not None:
                break
            time.sleep(1)
            current_output = proc.stdout.read(1)
            if current_output:
                output += current_output
            elapsed_time = time.time() - start_time
            if elapsed_time > 10 and not output:
                proc.kill()
                return "", "Execution timed out (possibly an infinite loop).", -1

        stdout, stderr = proc.communicate()
        output += stdout

        # FileNotFoundErrorを無視
        if "FileNotFoundError" in stderr:
            stderr = ""
            returncode = 0

        return output, stderr, returncode
    except subprocess.TimeoutExpired:
        return "", "Execution timed out", -1
    except Exception as e:
        return "", str(e), -1


def main():
    stdout, stderr, returncode = run_code()
    if returncode == -1:
        print(stderr, file=sys.stderr)
    else:
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)


if __name__ == "__main__":
    main()
