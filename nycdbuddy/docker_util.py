from typing import Union, List
import random
import docker


def run_and_remove(client: docker.DockerClient, image: str, cmd: Union[str, List[str]]) -> bytes:
    cname = f"nycdbuddy-run-{random.random()}"
    try:
        return client.containers.run(image, cmd, name=cname)
    finally:
        client.containers.get(cname).remove()


def exists(collection, name: str) -> bool:
    return len(collection.list(filters={'name': name})) > 0


def container_exists(client: docker.DockerClient, name: str) -> bool:
    return len(client.containers.list(all=True, filters={'name': name})) > 0


def remove_volume(client: docker.DockerClient, name: str) -> None:
    if exists(client.volumes, name):
        volume = client.volumes.get(name)
        print(f"Removing volume {volume.name}.")
        volume.remove()
