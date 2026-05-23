import pytest

try:
    from testcontainers.mongodb import MongoDbContainer

    @pytest.fixture(scope="session")
    def mongo_container():
        try:
            import docker as _docker
            _docker.from_env().ping()
        except Exception:
            pytest.skip("Docker is not available — skipping integration tests")

        with MongoDbContainer("mongo:7.0") as container:
            yield container

    @pytest.fixture
    def mongo_connection_url(mongo_container: MongoDbContainer) -> str:
        return mongo_container.get_connection_url()

except ImportError:
    pass
