from io import StringIO, BytesIO
from typing import TextIO, List, Optional, Dict, NamedTuple
import sys
import tarfile
import docker
import subprocess


TAG_NAME = 'nycdbuddy'

NYCDB_REPO = "https://github.com/aepyornis/nyc-db"

DOCKERFILE = """\
FROM python:3.6

RUN apt-get update \\
  && apt-get install -y \\
    unzip \\
    postgresql-client \\
  && rm -rf /var/lib/apt/lists/* \\
  && rm -rf /src/*.deb

ARG NYCDB_REPO
ARG NYCDB_REV

RUN curl -L ${NYCDB_REPO}/archive/${NYCDB_REV}.zip > nyc-db.zip \\
  && unzip nyc-db.zip \\
  && rm nyc-db.zip \\
  && mv nyc-db-${NYCDB_REV} nyc-db \\
  && cd nyc-db/src \\
  && pip install -e .

# Currently nyc-db mentions psycopg2 as a dependency, which is deprecated
# and will log lots of annoying warnings about using psycopg2-binary
# instead, so let's just install that to avoid the warnings.
RUN pip install psycopg2-binary
"""


class BuildArgs(NamedTuple):
    repo: str
    rev: str

    @property
    def short_rev(self) -> str:
        return self.rev[:10]

    def to_dockerfile_buildargs(self) -> Dict[str, str]:
        return {
            'NYCDB_REPO': self.repo,
            'NYCDB_REV': self.rev
        }


def build_context_tarfile(dockerfile: str) -> BytesIO:
    dockerfile_bytes = dockerfile.encode('utf-8')
    f = BytesIO()
    tar = tarfile.open(mode='w', fileobj=f)
    tarinfo = tarfile.TarInfo('Dockerfile')
    tarinfo.size = len(dockerfile_bytes)
    tar.addfile(tarinfo, BytesIO(dockerfile_bytes))
    tar.close()
    f.seek(0)
    return f


def get_latest_rev(repo: str, branch: str='master') -> str:
    stdout = subprocess.check_output([
        'git', 'ls-remote', repo, branch
    ])
    return stdout.decode('ascii').split()[0]


def get_lines_from_events(events) -> List[str]:
    return [event['stream'] for event in events if 'stream' in event]


def show_build_log(events, stderr: TextIO) -> None:
    stderr.write('-- BEGIN BUILD LOG --\n\n')
    for line in get_lines_from_events(events):
        stderr.write(line)
    stderr.write('\n\n-- END BUILD LOG --\n\n')


def build(
    client: docker.DockerClient,
    build_args: Optional[BuildArgs]=None,
    stderr: TextIO=sys.stderr
) -> str:
    if build_args is None:
        build_args = BuildArgs(repo=NYCDB_REPO, rev=get_latest_rev(NYCDB_REPO))
    context = build_context_tarfile(DOCKERFILE)
    print(f"Building image for {build_args.repo}@{build_args.short_rev}...")
    try:
        image, _ = client.images.build(
            tag=TAG_NAME,
            fileobj=context,
            custom_context=True,
            buildargs=build_args.to_dockerfile_buildargs()
        )
    except docker.errors.BuildError as e:
        stderr.write('Something bad happened. Here is the build log:\n\n')
        show_build_log(e.build_log, stderr)
        raise e
    _, image_id = image.short_id.split(':')
    image_tags = ', '.join(image.tags)
    print(f"Built image {image_id} with tags {image_tags}.")
    return image_id
