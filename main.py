import sys
import subprocess
import os
import signal
from replit import db
from analyzer import Analyzer
from bot_skynet import run

def main():
    # Create bots
    files = [
        "bot_skynet.py",
    ]
    procs = []

    for file in files:
        proc = subprocess.Popen(
            [sys.executable, file], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        procs.append(proc)
        print('-' * 5)
        print('{}'.format(file.replace('.py', '')))
        print('Started pid: {}'.format(proc.pid))

    # Await user input
    result = ''
    while result != 'ESTOP':
        result = input("Type ESTOP to Stop all...")
        print(result)

    # Kill all
    print("Attempting to stop subprocesses")
    for proc in procs:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    print("Finished stopping")


def api_test():
    analyze = Analyzer()
    res = analyze('Hello.')
    print(res)


def clear_db():
    db.clear()


if __name__ == '__main__':
    run()
