#!/usr/bin/env python3

# BID    - build id (run id)
# PID    - process id
# RUNNER - executable file (process)

import os
import random
import signal
import string
import subprocess
import sys

ASCII_ART = r"""
 _____                       __  __
/ ____|                     |  \/  |
| |  __  __ _ _______ _ __  | \  / | ___ _ __  _   _
| | |_ |/ _` |_  / _ \ '__| | |\/| |/ _ \ '_ \| | | |
| |__| | (_| |/ /  __/ |    | |  | |  __/ | | | |_| |
 \_____|\__,_/___\___|_|    |_|  |_|\___|_| |_|\__,_|
"""

GZR_DIR = ".gzr"


def show_ascii_art():
    print(ASCII_ART)


def show_status(txt: str):
    print(f"# {txt}")


def show_tui(txt: str):
    print(txt)


def ask_tui(txt: str) -> str:
    return input(f"> {txt}")


def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def write_file(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)


def find_runners():
    return sorted(
        f for f in os.listdir(".")
        if f.endswith(".gzr") and os.path.isfile(f)
    )


class Pid(object):
    def __init__(self, runner: str):
        self.__file = f"{GZR_DIR}/.{runner}.pid"

    def __str__(self):
        return str(self.__pid)

    def __refresh(self):
        try:
            self.__pid = int(read_file(self.__file))
        except Exception:
            self.__pid = None

    def remove(self):
        os.remove(self.__file)

    def update(self, process: subprocess.Popen):
        write_file(self.__file, str(process.pid))

    def kill(self):
        self.__refresh()
        try:
            pgid = os.getpgid(self.__pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception as e:
            show_status(f"No process with pid ${self.__pid}")

    def running(self) -> bool:
        self.__refresh()
        try:
            os.kill(self.__pid, 0)
        except Exception:
            return False
        else:
            return True


class Bid(object):
    def __init__(self, runner: str):
        self.__file = f"{GZR_DIR}/.{runner}.bid"

    def __str__(self):
        return read_file(self.__file)

    def remove(self):
        os.remove(self.__file)

    def update(self):
        write_file(self.__file, self.__gen_bid())

    @staticmethod
    def __gen_bid():
        return " ".join(random.choices(string.ascii_uppercase + string.digits, k=5))


class Log(object):
    def __init__(self, runner: str):
        self.__file = f"{GZR_DIR}/.{runner}.log"

    def output(self) -> str:
        return self.__file

    def remove(self):
        os.remove(self.__file)


def log_pid_bid(runner: str) -> (Log, Pid, Bid):
    log = Log(runner)
    pid = Pid(runner)
    bid = Bid(runner)
    return log, pid, bid


def start_runner(runner: str, log: Log, pid: Pid, bid: Bid):
    if pid.running():
        show_status(f"Process with pid ${pid} already running")
        sys.exit(1)

    if not os.access(runner, os.X_OK):
        os.chmod(runner, 0o755)

    with open(log.output(), "w") as f:
        proc = subprocess.Popen(
            ["bash", runner],
            stdout=f,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )

    pid.update(proc)
    bid.update()

    show_status("Success")


def stop_runner(pid: Pid, log: Log, bid: Bid):
    if not pid.running():
        show_status(f"Process with pid ${pid} not running")
        sys.exit(1)

    pid.kill()
    pid.remove()
    log.remove()
    bid.remove()

    show_status("Success")


def restart_runner(runner: str, log: Log, pid: Pid, bid: Bid):
    stop_runner(pid, log, bid)
    start_runner(runner, log, pid, bid)


def interactive(runners: list[str]):
    def choose_runner():
        show_tui("Found multiple runners:")
        for i, c in enumerate(runners, 1):
            show_tui(f"{i}) {c}")
        while True:
            choice = ask_tui(f"Choose a runner (1-{len(runners)}): ").strip()
            if choice == "":
                sys.exit(0)
            if choice.isdigit() and 1 <= int(choice) <= len(runners):
                return runners[int(choice) - 1]
            show_status("Please choose a valid option.")

    if len(runners) > 1:
        runner = choose_runner()
    else:
        runner = runners[0]

    log, pid, bid = log_pid_bid(runner)

    running = pid.running()

    if running:
        show_tui(f"                                      > {bid} <")

    commands = {
        True: ["Restart", "Stop"],
        False: ["Start"]
    }[running]

    show_tui(f"Actions for '{runner}':")
    show_tui("\n".join([f"{i + 1}) {c}" for i, c in enumerate(commands)]))

    cmd_num = None
    while True:
        try:
            cmd_text = ask_tui(f"Enter command number {tuple(range(1, len(commands) + 1))}: ").strip()
            if cmd_text == "":
                sys.exit(0)
            cmd_num = int(cmd_text)
            _ = commands[cmd_num]
            break
        except Exception as _:
            show_status("Please enter a valid number.")
            continue

    if running:
        if cmd_num == 1:
            restart_runner(runner, log, pid, bid)
        elif cmd_num == 2:
            stop_runner(pid, log, bid)
    else:
        start_runner(runner, log, pid, bid)

    show_status("Success")


def inline_mode(args: list[str], runners: list[str]):
    if len(args) == 1:
        action = args[0]
        if action not in ["start", "stop", "restart"]:
            show_status("Invalid argument. Usage:")
            show_status("gazer start|stop|restart")
            show_status("gazer <config-name> start|stop|restart")
            sys.exit(1)

        if len(runners) == 1:
            runner = runners[0]
        else:
            show_status("Multiple configuration files found, specify configuration name.")
            show_status("Usage: gazer <config-name> start|stop|restart")
            sys.exit(1)
    elif len(args) == 2:
        config_arg, action = args
        if action not in ["start", "stop", "restart"]:
            show_status(f"Invalid action '{action}'. Use start, stop or restart.")
            sys.exit(1)
        runner = None
        for c in runners:
            if c[:-6] == config_arg:
                runner = c
                break
        if not runner:
            show_status(f"Configuration file for '{config_arg}' not found.")
            sys.exit(1)
    else:
        show_status("Too many arguments.")
        show_status("Usage: gazer start|stop|restart")
        show_status("   or: gazer <config-name> start|stop|restart")
        sys.exit(1)

    log, pid, bid = log_pid_bid(runner)

    if action == "start":
        start_runner(runner, log, pid, bid)
    elif action == "stop":
        stop_runner(pid, log, bid)
    elif action == "restart":
        restart_runner(runner, log, pid, bid)


def main(args: list[str]):
    show_ascii_art()

    runners = find_runners()
    if not runners:
        show_status("No '*.gzr' runner files found!")
        sys.exit(1)

    if args:
        inline_mode(args, runners)
        return

    interactive(runners)


if __name__ == "__main__":
    os.makedirs(GZR_DIR, exist_ok=True)

    main(sys.argv[1:])
