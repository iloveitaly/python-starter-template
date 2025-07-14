import re
import random
import subprocess
import logging
from pathlib import Path
import socket
import shutil

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

LOCAL_HOST = '127.0.0.1'
MIN_BASE = 83
MAX_BASE = 650
PORT_MULTIPLIER = 100
MAX_ATTEMPTS = 10
ALIASES_FILE = '.localias.yaml'
FAST_MOD_TOOL = 'fastmod'

def main() -> None:
    if shutil.which(FAST_MOD_TOOL) is None:
        log.error(f"{FAST_MOD_TOOL} is not installed, please install it")
        raise SystemExit(1)

    content = Path(ALIASES_FILE).read_text()

    ports: list[int] = [int(p) for p in re.findall(r': (\d+)', content)]
    if not ports:
        log.info(f"no ports found in {ALIASES_FILE}")
        return

    base: int = min(ports)
    new_base = select_new_base_port(base, ports)
    log.info("selected new base port %s", new_base)

    for port in ports:
        offset: int = port - base
        new_port: int = new_base + offset
        log.info("replacing port %s with new port %s", port, new_port)
        subprocess.run([FAST_MOD_TOOL, str(port), str(new_port), '--hidden', "--glob", "!.copier/*", "--glob", "!.git/**", "--glob", "!uv.lock", "--glob", "!pnpm-lock.yaml"], check=True)

def select_new_base_port(base: int, ports: list[int]) -> int:
    attempts: int = 0
    while attempts < MAX_ATTEMPTS:
        new_base = random.randint(MIN_BASE, MAX_BASE) * PORT_MULTIPLIER
        new_ports = [new_base + (p - base) for p in ports]
        if all(is_port_available(p) for p in new_ports):
            return new_base
        attempts += 1
    log.error("could not find available ports after 10 attempts")
    raise SystemExit(1)

def is_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((LOCAL_HOST, port))
        return True
    except OSError:
        return False

if __name__ == '__main__':
    main()
