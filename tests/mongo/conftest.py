import random
from typing import Iterator

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs


class CustomDockerContainer(DockerContainer):
    def __init__(self, image: str, connection_url: str, **kwargs) -> None:
        super().__init__(image, **kwargs)
        self.connection_url = connection_url


@pytest.fixture(scope="session")
def mongo() -> Iterator[CustomDockerContainer]:

    mongo_bind_port = random.randint(a=30000, b=40000)
    connection_url = f"mongodb://localhost:{mongo_bind_port}/?replicaSet=rs"

    mongo_container = CustomDockerContainer("mongo:7.0", connection_url)

    mongo_container.with_bind_ports(container=mongo_bind_port, host=mongo_bind_port)
    mongo_container.with_command(f"--port={mongo_bind_port} --replSet=rs")
    mongo_container.start()
    # rs.initiate падает, пока mongod не начал принимать соединения
    wait_for_logs(mongo_container, "Waiting for connections")

    rs_initiate = (
        "mongosh --quiet --eval=\"rs.initiate({_id:'rs',members:[{_id:0,host:'localhost:%s'}]})\" mongodb://localhost:%s"
        % (mongo_bind_port, mongo_bind_port)
    )

    exit_code, output = mongo_container.exec(rs_initiate)
    if exit_code != 0:
        raise RuntimeError(f"replica set didn't get setup properly: {output.decode()}")

    yield mongo_container

    mongo_container.stop()
