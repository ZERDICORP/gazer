#!/usr/bin/env python3

# BID    - build id (run id)
# PID    - process id
# CONFIG - executable file (process)

import os
import random
import signal
import string
import subprocess
import sys

ASCII_ART = r"""
 _____                      __  __
/ ____|                    |  \/  |
| |  __  __ _ _______ _ __  | \  / | ___ _ __  _   _
| | |_ |/ _` |_  / _ \ '__| | |\/| |/ _ \ '_ \| | | |
| |__| | (_| |/ /  __/ |    | |  | |  __/ | | | |_| |
 \_____|\__,_/___\___|_|    |_|  |_|\___|_| |_|\__,_|
"""


def show_ascii_art():
    print(ASCII_ART)


def find_configs():
    return sorted(f for f in os.listdir(".") if f.endswith(".gzr"))


def read_file(path: str):
    with open(path, "r") as f:
        return f.read().strip()


def write_file(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)


def gen_bid():
    return " ".join(random.choices(string.ascii_uppercase + string.digits, k=5))


def is_active(pid: int):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def log_pid_bid(cfg_name: str) -> (str, str, str):
    log_file = f".{cfg_name}.log"
    pid_file = f".{cfg_name}.pid"
    bid_file = f".{cfg_name}.bid"
    return log_file, pid_file, bid_file


def kill_process_group(pid: int):
    try:
        pgid = os.getpgid(pid)
        os.killpg(pgid, signal.SIGKILL)
    except Exception:
        print(f"No process with pid ${pid}")


def start_config(selected_config: str, log_file: str, pid_file: str, bid_file: str):
    pid = int(read_file(pid_file))
    if is_active(pid):
        print(f"Process with pid ${pid} already running")
        sys.exit(1)

    if not os.access(selected_config, os.X_OK):
        os.chmod(selected_config, 0o755)

    with open(log_file, "ab") as f:
        proc = subprocess.Popen(
            ["bash", selected_config],
            stdout=f,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    write_file(pid_file, str(proc.pid))
    write_file(bid_file, gen_bid())

    print("Success")


def stop_config(pid_file: str, log_file: str, bid_file: str):
    pid = int(read_file(pid_file))
    if not is_active(pid):
        print(f"Process with pid ${pid} not running")
        sys.exit(1)

    kill_process_group(pid)
    for f in [pid_file, log_file, bid_file]:
        os.remove(f)
    print("Success")


def restart_config(selected_config, log_file, pid_file, bid_file):
    stop_config(pid_file, log_file, bid_file)
    start_config(selected_config, log_file, pid_file, bid_file)


def choose_config_interactive(configs):
    print("Found multiple configuration files:")
    for i, c in enumerate(configs, 1):
        print(f"{i}) {c}")
    while True:
        choice = input(f"Choose a configuration file (1-{len(configs)}): ").strip()
        if choice == "":
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(configs):
            return configs[int(choice) - 1]
        print("Please choose a valid option.")


def interactive(configs: list[str]):
    if len(configs) > 1:
        cfg_name = choose_config_interactive(configs)
    else:
        cfg_name = configs[0]

    log_file, pid_file, bid_file = log_pid_bid(cfg_name)

    if os.path.isfile(bid_file):
        build_id = read_file(bid_file)
        print(f"                                      > {build_id} <")

    print(f"Actions for '{cfg_name}':")

    if os.path.isfile(pid_file):
        started = True
        print("1) Restart")
        print("2) Stop")
        if not os.path.isfile(log_file):
            open(log_file, "a").close()
    else:
        started = False
        print("1) Start")

    while True:
        if started:
            input_str = input("Enter command number (1, 2): ").strip()
        else:
            input_str = input("Enter command number (1): ").strip()
        if input_str == "":
            sys.exit(0)
        if input_str in ["1", "2"]:
            cmd = input_str
            break
        else:
            print("Please enter a valid number.")

    if os.path.isfile(pid_file):
        pid = int(read_file(pid_file))
        if is_active(pid):
            if cmd == "2":
                kill_process_group(pid)
                for f in [pid_file, log_file, bid_file]:
                    os.remove(f)
                print("Success")
                sys.exit(0)
            elif cmd == "1":
                kill_process_group(pid)

    if cmd == "2":
        for f in [pid_file, log_file, bid_file]:
            os.remove(f)
        print("Success")
        sys.exit(1)

    start_config(cfg_name, log_file, pid_file, bid_file)


def inline_mode(args: list[str], configs: list[str]):
    if len(args) == 1:
        action = args[0]
        if action not in ["start", "stop", "restart"]:
            print("Invalid argument. Usage:")
            print("gazer start|stop|restart")
            print("gazer <config-name> start|stop|restart")
            sys.exit(1)

        if len(configs) == 1:
            cfg_name = configs[0]
        else:
            print("Multiple configuration files found, specify configuration name.")
            print("Usage: gazer <config-name> start|stop|restart")
            sys.exit(1)
    elif len(args) == 2:
        config_arg, action = args
        if action not in ["start", "stop", "restart"]:
            print(f"Invalid action '{action}'. Use start, stop or restart.")
            sys.exit(1)
        cfg_name = None
        for c in configs:
            if c[:-6] == config_arg:
                cfg_name = c
                break
        if not cfg_name:
            print(f"Configuration file for '{config_arg}' not found.")
            sys.exit(1)
    else:
        print("Too many arguments.")
        print("Usage: gazer start|stop|restart")
        print("   or: gazer <config-name> start|stop|restart")
        sys.exit(1)

    log_file, pid_file, bid_file = log_pid_bid(cfg_name)

    if action == "start":
        start_config(cfg_name, log_file, pid_file, bid_file)
    elif action == "stop":
        stop_config(pid_file, log_file, bid_file)
    elif action == "restart":
        restart_config(cfg_name, log_file, pid_file, bid_file)
    sys.exit(0)


def main(args: list[str]):
    show_ascii_art()

    configs = find_configs()
    if not configs:
        print("No '*.gzr' configuration files found!")
        sys.exit(1)

    if args:
        inline_mode(args, configs)
        return

    interactive(configs)


if __name__ == "__main__":
    main(sys.argv[1:])
