from abc import ABC
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import CollectionInvalid, ServerSelectionTimeoutError

from src.conf_logger import setup_logger
from src.config import DEBUG, MONGO_ADMIN_URI, MONGO_COLLECTION, MONGO_DB, MONGO_WRITER_URI
from src.core.documentstorage.exceptions import MongoDBConnectorError
from src.core.documentstorage.models import OCRedImageResult

logger = setup_logger(__name__, "documentstorage")

_UNSUPPORTED_MONGO_KEYWORDS = frozenset({"format", "title", "$schema", "examples"})


def _strip_unsupported_schema_keywords(node: Any) -> None:
    """Recursively remove JSON Schema keywords rejected by MongoDB's $jsonSchema validator.

    Limitation: models with nested Pydantic models generate $defs + $ref pointers.
    Stripping $defs alone leaves dangling $ref values — nested models require $ref
    inlining before this function would work correctly with MongoDB.
    """
    if isinstance(node, dict):
        for key in _UNSUPPORTED_MONGO_KEYWORDS:
            node.pop(key, None)
        for value in node.values():
            _strip_unsupported_schema_keywords(value)
    elif isinstance(node, list):
        for item in node:
            _strip_unsupported_schema_keywords(item)


class MongoConnectorContextManager(ABC):  # noqa B024
    def __new__(cls, *args, **kwargs):
        """
        @abstractmethod can not decorate __init__, which in this case should be reimplemented.
        """
        if cls is MongoConnectorContextManager:
            raise TypeError("MongoConnectorContextManager cannot be instantiated directly")
        return super().__new__(cls)

    def __init__(self, mongo_uri: str, mongo_db: str):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client: AsyncMongoClient | None = None
        self.database: Any = None

    async def __aenter__(self):
        try:
            self.client = AsyncMongoClient(self.mongo_uri, uuidRepresentation="standard")
            self.database = self.client[self.mongo_db]
            await self.client.server_info()
            return self

        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB Client connection error at connector instantiation: {e}")
            message = str(e) if DEBUG else ""
            raise MongoDBConnectorError(message=message) from e

        except Exception as e:
            logger.error(f"Unexpected MongoDB Client instantiation Error: {e}")
            message = f"Unexpected Error during mongodb connector instantiation {str(e)}" if DEBUG else "Unexpected Error"
            raise MongoDBConnectorError(message=message) from e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            await self.client.close()
        self.client = None

    async def ensure_non_admin_user(self):
        if self.database is None:
            raise MongoDBConnectorError(message="Database connection not initialized")
        try:
            result = await self.database.command("usersInfo", {"forAllDBs": False})
        except Exception as e:
            message = "Error during getting user role"
            logger.error(f"{message}: {e}")
            raise MongoDBConnectorError(message=message) from e

        users = result.get("users", [])
        if not users:
            raise MongoDBConnectorError(message="No users found for the current database connection")

        forbidden_roles = {"dbAdmin", "userAdmin", "readWriteAnyDatabase", "dbOwner", "root", "clusterAdmin"}
        for role in users[0].get("roles", []):
            if role["role"] in forbidden_roles or role["role"].endswith("Admin"):
                raise MongoDBConnectorError(message=f"User role not allowed: {role['role']} on the base: {role['db']}")


class MongoConnectorBuilder(MongoConnectorContextManager):
    def __init__(
        self, mongo_uri: str = MONGO_ADMIN_URI, mongo_db: str = MONGO_DB, mongo_collection: str = MONGO_COLLECTION
    ):
        super().__init__(mongo_uri, mongo_db)
        self.mongo_collection = mongo_collection

    async def initialize(self):
        async with self:
            if self.client is None or self.database is None:
                raise MongoDBConnectorError(message="Database connection not initialized")

            collection_list = await self.database.list_collection_names()
            collection_exists = self.mongo_collection in collection_list

            if not collection_exists:
                schema = OCRedImageResult.model_json_schema()
                _strip_unsupported_schema_keywords(schema)
                validator = {"$jsonSchema": schema}

                try:
                    await self.database.create_collection(
                        self.mongo_collection, validator=validator, validationLevel="strict", validationAction="error"
                    )
                    logger.info(
                        f"Successfully created collection '{self.mongo_collection}' in database '{self.mongo_db}' "
                        f"with schema validation."
                    )
                except CollectionInvalid as e:
                    logger.warning(
                        f"Collection '{self.mongo_collection}' already exists in database '{self.mongo_db}'. "
                        f"Skipping creation. Error: {e}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to create collection '{self.mongo_collection}' "
                        f"with validation in database '{self.mongo_db}': {e}"
                    )
                    raise MongoDBConnectorError(
                        message=f"Failed to create collection '{self.mongo_collection}': {e}"
                    ) from e

            await self.enable_sharding()

    async def enable_sharding(self):
        if self.client is None:
            raise MongoDBConnectorError(message="Database connection not initialized")
        shard_key = {"_id": 1}
        try:
            config_db = self.client["config"]
            existing = await config_db["collections"].find_one({"_id": f"{self.mongo_db}.{self.mongo_collection}"})
            if existing and existing.get("sharded", False):
                logger.info(f"Collection '{self.mongo_collection}' is already sharded.")
            else:
                await self.client.admin.command(
                    "shardCollection", f"{self.mongo_db}.{self.mongo_collection}", key=shard_key
                )
                logger.info(f"Sharding enabled for collection '{self.mongo_collection}' with shard key: {shard_key}.")
        except Exception as e:
            logger.error(f"Failed to enable sharding for collection '{self.mongo_collection}': {e}")
            raise MongoDBConnectorError(message=f"Failed to enable sharding: {e}") from e


class MongoConnectorRunner(MongoConnectorContextManager):
    def __init__(
        self, mongo_uri: str = MONGO_WRITER_URI, mongo_db: str = MONGO_DB, mongo_collection: str = MONGO_COLLECTION
    ) -> None:
        super().__init__(mongo_uri, mongo_db)
        self.mongo_collection = mongo_collection

    async def __aenter__(self):
        await super().__aenter__()
        if not DEBUG:
            await self.ensure_non_admin_user()
        return self

    async def upload_ocr_result(self, image_name: str, ocr_result: list[str], user_email: str) -> str:
        if self.database is None:
            raise MongoDBConnectorError(message="Database connection not initialized")
        try:
            document_data = OCRedImageResult(user_email=user_email, filename=image_name, ocr_result=ocr_result)
            doc_to_insert = document_data.model_dump(by_alias=True, mode="json")

            collection = self.database[self.mongo_collection]
            insert_result = await collection.insert_one(doc_to_insert)
            inserted_id = insert_result.inserted_id

            logger.info(f"Successfully uploaded OCR result for '{image_name}' with id '{inserted_id}'.")
            return str(inserted_id)

        except Exception as e:
            logger.error(f"Failed to upload OCR result for '{image_name}': {e}")
            raise MongoDBConnectorError(message=f"Failed to upload OCR data: {e}") from e
