from typing import NamedTuple, Dict
import urllib.parse
import docker
import psycopg2


POSTGRES_VERSION = '11'

IMAGE = f'postgres:{POSTGRES_VERSION}'

CONTAINER_NAME = 'nycdbuddy_db'

VOLUME_NAME = 'nycdbuddy_pgdata'


class ConnectInfo(NamedTuple):
    user: str = 'nycdb'
    db: str = 'nycdb'
    password: str = 'nycdb'
    host: str = 'localhost'

    def with_docker_host(self, client: docker.DockerClient) -> 'ConnectInfo':
        info = urllib.parse.urlparse(client.api.base_url)
        host = info.hostname if info.scheme == 'https' else 'localhost'
        return self._replace(host=host)

    def to_postgres_environment(self) -> Dict[str, str]:
        return {
            'POSTGRES_USER': self.user,
            'POSTGRES_PASSWORD': self.password,
            'POSTGRES_DB': self.db,
        }

    def to_psycopg2_kwargs(self) -> Dict[str, str]:
        return {
            'dbname': self.db,
            'user': self.user,
            'password': self.password,
            'host': self.host
        }


def hello_world(client: docker.DockerClient, cinfo: ConnectInfo=ConnectInfo()) -> None:
    cinfo = cinfo.with_docker_host(client)
    print(f'Connecting to db on "{cinfo.host}"...')
    with psycopg2.connect(**cinfo.to_psycopg2_kwargs()) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT usename FROM pg_user')
            print(f'Connected to db and found a user named "{cur.fetchone()[0]}".')


def stop(client: docker.DockerClient, name: str=CONTAINER_NAME) -> None:
    containers = client.containers.list(filters={'name': name})
    if containers:
        c = containers[0]
        print(f"Stopping postgres container '{name}'...")
        c.stop()
        print(f"Removing postgres container '{name}'...")
        c.remove()


def start(
    client: docker.DockerClient,
    cinfo: ConnectInfo=ConnectInfo(),
    name: str=CONTAINER_NAME,
    volume_name: str=VOLUME_NAME
) -> None:
    stop(client, name)
    print(f"Starting postgres container '{name}' with volume '{volume_name}'...")
    client.containers.run(
        IMAGE,
        name=name,
        environment=cinfo.to_postgres_environment(),
        volumes={
            volume_name: {
                'bind': '/var/lib/postgresql/data',
                'mode': 'rw'
            }
        },
        ports={
            '5432/tcp': ('0.0.0.0', '5432')
        },
        detach=True
    )
    print("Done.")
