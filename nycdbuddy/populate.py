from typing import List, NamedTuple, Optional, Dict, Any
import sys
import yaml
import docker

from . import image, postgres, docker_util


CONTAINER_NAME = 'nycdbuddy_populate'

NETWORK_NAME = f'${CONTAINER_NAME}_network'

DATASETS_YML = '/nyc-db/src/nycdb/datasets.yml'

TEST_DATA_DIR = '/nyc-db/src/tests/integration/data'

NYCDB_DATA_DIR = '/var/nycdb'

# Status when a container has already exited.
CONTAINER_EXITED = 'exited'


class TableInfo(NamedTuple):
    name: str
    dataset: str
    rows: Optional[int] = None

    def with_rows(self, cursor) -> 'TableInfo':
        if does_table_exist(cursor, self.name):
            cursor.execute(f'SELECT COUNT(*) FROM {self.name}')
            count = cursor.fetchone()[0]
            return self._replace(rows=count)
        else:
            return self._replace(rows=None)

    def describe(self) -> str:
        if self.name == self.dataset:
            name = self.name
        else:
            name = f"{self.name} ({self.dataset})"
        if self.rows is None:
            return f"Table {name} does not currently exist."
        return f"Table {name} has {self.rows:,} rows."


def get_datasets_yml(
    client: docker.DockerClient,
    image: str
) -> Dict[str, Any]:
    result = docker_util.run_and_remove(client, image, f'cat {DATASETS_YML}')
    return yaml.load(result.decode('utf-8'))


def get_dataset_tables(yml: Dict[str, Any]) -> List[TableInfo]:
    result: List[TableInfo] = []
    for dataset_name, info in yml.items():
        schema = info['schema']
        if isinstance(schema, dict):
            schemas = [schema]
        else:
            schemas = schema
        for schema in schemas:
            result.append(TableInfo(name=schema['table_name'], dataset=dataset_name))
    return result


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


def does_table_exist(cursor, table: str) -> bool:
    # https://stackoverflow.com/a/1874268
    query = f"select exists(select * from information_schema.tables where table_name='{table}')"
    cursor.execute(query)
    return cursor.fetchone()[0]


def show_rowcounts(
    client: docker.DockerClient,
    cinfo: postgres.ConnectInfo,
    nycdb_image: str
):
    ds = get_datasets_yml(client, nycdb_image)
    tables = get_dataset_tables(ds)
    with postgres.get_connection(client, cinfo) as conn:
        for table in tables:
            with conn.cursor() as cur:
                table = table.with_rows(cur)
                print(table.describe())


def status(
    client: docker.DockerClient,
    container_name: str=CONTAINER_NAME,
    nycdb_image: str=image.TAG_NAME,
    cinfo: postgres.ConnectInfo=postgres.ConnectInfo()
) -> None:
    if not docker_util.container_exists(client, container_name):
        print("No populate process currently exists.")
        return
    container = client.containers.get(container_name)
    if container.status == CONTAINER_EXITED:
        exitinfo = container.wait()
        if exitinfo['Error'] is None and exitinfo['StatusCode'] == 0:
            print("Populate exited successfully!")
        else:
            print("Populate failed:")
            print(get_logs(container))
    else:
        print(f"Populate process container {container_name} is {container.status}.\n")
        show_rowcounts(client, cinfo=cinfo, nycdb_image=nycdb_image)


def populate(
    client: docker.DockerClient,
    use_test_data: bool=False,
    nycdb_image: str=image.TAG_NAME,
    container_name: str=CONTAINER_NAME,
    postgres_container_name: str=postgres.CONTAINER_NAME,
    cinfo: postgres.ConnectInfo=postgres.ConnectInfo()
) -> None:
    if docker_util.container_exists(client, container_name):
        container = client.containers.get(container_name)
        if container.status == CONTAINER_EXITED:
            container.remove()
        else:
            print("A populate process is already running.")
            sys.exit(1)
    if not docker_util.container_exists(client, postgres_container_name):
        postgres.start(client, cinfo=cinfo, name=postgres_container_name)
    db_container = client.containers.get(postgres_container_name)
    datasets = get_datasets(client, nycdb_image)
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
        nycdb_image,
        ['bash', '-c', command],
        name=container_name,
        network=network.name,
        detach=True
    )

    print(f"Started populate process in container '{container_name}'.")
