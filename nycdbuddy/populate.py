from typing import List
import docker

from . import image, postgres, docker_util


CONTAINER_NAME = 'nycdbuddy_populate'

NETWORK_NAME = f'${CONTAINER_NAME}_network'

TEST_DATA_DIR = '/nyc-db/src/tests/integration/data'

NYCDB_DATA_DIR = '/var/nycdb'


def get_datasets(
    client: docker.DockerClient,
    image: str
) -> List[str]:
    result = docker_util.run_and_remove(client, image, 'nycdb --list-datasets')
    return result.decode('ascii').splitlines()


def get_or_create_network(client: docker.DockerClient):
    if not docker_util.exists(client.networks, NETWORK_NAME):
        client.networks.create(NETWORK_NAME)
    return client.networks.get(NETWORK_NAME)


def get_logs(container) -> str:
    return container.logs().decode('utf-8', errors='ignore')


def status(
    client: docker.DockerClient,
    container_name: str=CONTAINER_NAME,
) -> None:
    if not docker_util.container_exists(client, container_name):
        print("No populate process currently exists.")
        return
    container = client.containers.get(container_name)
    if container.status == 'exited':
        exitinfo = container.wait()
        if exitinfo['Error'] is None and exitinfo['StatusCode'] == 0:
            print("Populate exited successfully!")
        else:
            print("Populate failed:")
            print(get_logs(container))
        print(f"Removing container {container_name}.")
        container.remove()
    else:
        print(f"Populate process container {container_name} is {container.status}.")
        lines = get_logs(container).splitlines()[:-5]
        print(f"Here's its latest output:\n")
        print('\n'.join(lines))


def populate(
    client: docker.DockerClient,
    use_test_data: bool=False,
    nycdb_image_tag_name: str=image.TAG_NAME,
    container_name: str=CONTAINER_NAME,
    postgres_container_name: str=postgres.CONTAINER_NAME,
    cinfo: postgres.ConnectInfo=postgres.ConnectInfo()
) -> None:
    if not use_test_data:
        raise NotImplementedError()
    if docker_util.container_exists(client, container_name):
        print("A previous populate process already exists.")
        status(client, container_name)
        return
    db_container = client.containers.get(postgres_container_name)
    datasets = get_datasets(client, nycdb_image_tag_name)
    nycdb_cmd = ' '.join([
        'nycdb',
        '-D', cinfo.db,
        '-H', postgres_container_name,
        '-U', cinfo.user,
        '-P', cinfo.password,
        '--root-dir', TEST_DATA_DIR if use_test_data else NYCDB_DATA_DIR,
    ])
    network = get_or_create_network(client)

    if db_container not in network.containers:
        network.connect(db_container)

    command = ' && '.join(
        f'{nycdb_cmd} --download {dataset} && {nycdb_cmd} --load {dataset}'
        for dataset in datasets
    )

    container = client.containers.run(
        nycdb_image_tag_name,
        ['bash', '-c', command],
        name=container_name,
        network=network.name,
        detach=True
    )

    print(f"Started populate process in container '{container_name}'.")
