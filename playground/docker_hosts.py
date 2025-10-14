#!/usr/bin/env -S uv run --script
#
# /// script
# dependencies = [
#   "click",
#   "docker",
#   "structlog-config",
# ]
# ///

import click
from pathlib import Path

import docker
from structlog_config import configure_logger

start_pattern = "### Start Docker Domains ###\n"
end_pattern = "### End Docker Domains ###\n"
hosts: dict = {}


@click.command()
@click.argument('file', default='/etc/hosts')
@click.option('--dry-run', is_flag=True, help='Simulate updates without writing to file')
@click.option('--tld', default='localhost', show_default=True, help='TLD to append to domains')
@click.option('--listen', is_flag=True, help='Listen for container events and update continuously')
def main(file, dry_run, tld, listen):
    log = configure_logger()
    client = docker.from_env()
    load_running_containers(client)
    update_hosts_file(file, log, dry_run, tld)

    if not listen:
        return

    process_events(client, file, log, dry_run, tld)


def load_running_containers(client):
    for container in client.containers.list():
        hosts[container.id] = get_container_data(container.attrs)


def process_events(client, file, log, dry_run, tld):
    for event in client.events(decode=True):
        if event.get("Type") != "container":
            continue

        status = event.get("status")
        container_id = event.get("id")

        if status == "start":
            info = client.api.inspect_container(container_id)
            hosts[container_id] = get_container_data(info)
            update_hosts_file(file, log, dry_run, tld)
            continue

        if status in ("stop", "die", "destroy", "kill"):
            hosts.pop(container_id, None)
            update_hosts_file(file, log, dry_run, tld)
            continue

        if status == "rename":
            info = client.api.inspect_container(container_id)
            hosts[container_id] = get_container_data(info)
            update_hosts_file(file, log, dry_run, tld)


def get_container_data(info: dict) -> list[dict]:
    container_hostname = info["Config"]["Hostname"]
    container_name = info["Name"].strip("/")
    container_ip = info["NetworkSettings"]["IPAddress"]

    if info["Config"]["Domainname"]:
        container_hostname = f"{container_hostname}.{info['Config']['Domainname']}"

    result = []

    for values in info["NetworkSettings"]["Networks"].values():
        if not values["Aliases"]:
            continue

        result.append(
            {
                "ip": values["IPAddress"],
                "name": container_name,
                "domains": set(values["Aliases"] + [container_name, container_hostname]),
            }
        )

    if container_ip:
        result.append(
            {
                "ip": container_ip,
                "name": container_name,
                "domains": [container_name, container_hostname],
            }
        )

    return result


def update_hosts_file(hosts_path: str, log, dry_run: bool, tld: str):
    if not hosts:
        log.info("Removing all hosts before exit")
    else:
        log.info("Updating hosts file")
        for addresses in hosts.values():
            for addr in addresses:
                log.info("Host entry", ip=addr["ip"], domains=addr["domains"])

    lines = Path(hosts_path).read_text().splitlines(keepends=True)

    for i, line in enumerate(lines):
        if line == start_pattern:
            lines = lines[:i]
            break

    while lines and not lines[-1].strip():
        lines.pop()

    added_lines = []
    if hosts:
        added_lines.append(f"\n\n{start_pattern}")
        for addresses in hosts.values():
            for addr in addresses:
                suffixed_domains = [f"{d}.{tld}" for d in addr["domains"]]
                added_lines.append(f"{addr['ip']}    {'   '.join(sorted(suffixed_domains))}\n")
        added_lines.append(f"{end_pattern}\n")

    if dry_run:
        print(''.join(added_lines))
        return

    lines.extend(added_lines)
    proposed_content = ''.join(lines)
    log.info("Proposed hosts content", content=proposed_content)

    aux_path = Path(hosts_path).with_suffix('.aux')
    aux_path.write_text(proposed_content)
    aux_path.replace(Path(hosts_path))


if __name__ == "__main__":
    main()
