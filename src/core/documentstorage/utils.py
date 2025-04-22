from abc import ABC

from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, ServerSelectionTimeoutError

from src.conf_logger import setup_logger
from src.config import DEBUG, MONGO_ADMIN_URI, MONGO_COLLECTION, MONGO_DB, MONGO_WRITER_URI
from src.core.documentstorage.exceptions import MongoDBConnectorError
from src.core.documentstorage.models import OCRedImageResult

logger = setup_logger(__name__, "documentstorage")


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
        self.client = None
        self.database = None

    def __enter__(self):
        try:
            self.client = MongoClient(self.mongo_uri, uuidRepresentation='standard')
            self.database = self.client[self.mongo_db]
            self.client.server_info()
            return self

        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB Client connection error at connector instantiation: {e}")
            message = str(e) if DEBUG else ""
            raise MongoDBConnectorError(message=message) from e

        except Exception as e:
            logger.error(f"Unexpected MongoDB Client instantiation Error: {e}")
            message = f"Unexpected Error during mongodb connector instantiation {str(e)}" if DEBUG else "Unexpected Error"
            raise MongoDBConnectorError(message=message) from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        self.client = None

    def ensure_non_admin_user(self):
        try:
            result = self.database.command("usersInfo", {"forAllDBs": False})
            roles = result.get("users", [])[0].get("roles", [])

            forbidden_roles = {"dbAdmin", "userAdmin", "readWriteAnyDatabase", "dbOwner", "root", "clusterAdmin"}

            for role in roles:
                if role["role"] in forbidden_roles or role["role"].endswith("Admin"):
                    raise MongoDBConnectorError(message=f"User role not allowed: {role['role']} "
                                                        f"on the base: {role['db']}")

        except Exception as e:
            message = "Error during getting user role"
            logger.error(f"{message}: {e}")
            raise MongoDBConnectorError(message=message) from e

class MongoConnectorBuilder(MongoConnectorContextManager):
    def __init__(self, mongo_uri: str = MONGO_ADMIN_URI, mongo_db: str = MONGO_DB,
                 mongo_collection: str = MONGO_COLLECTION):
        super().__init__(mongo_uri, mongo_db)
        self.mongo_collection = mongo_collection
        with self:
            db_list = self.client.list_database_names()  # type: ignore[attr-defined]
            db_exists = self.mongo_db in db_list

            if not db_exists:
                schema = OCRedImageResult.model_json_schema()
                schema.pop("title", None)
                validator = {'$jsonSchema': schema}

                try:
                    self.database.create_collection(  # type: ignore[attr-defined]
                        self.mongo_collection,
                        validator=validator,
                        validationLevel="strict",
                        validationAction="error"
                    )
                    logger.info(
                        f"Successfully created collection '{self.mongo_collection}' in database '{self.mongo_db}' "
                        f"with schema validation.")
                    self.enable_sharding()

                except CollectionInvalid as e:
                    logger.warning(
                        f"Collection '{self.mongo_collection}' already exists in database '{self.mongo_db}'. "
                        f"Skipping creation. Error: {e}")
                    self.enable_sharding()
                    pass
                except Exception as e:
                    logger.error(
                        f"Failed to create collection '{self.mongo_collection}' "
                        f"with validation in database '{self.mongo_db}': {e}")
                    raise MongoDBConnectorError(
                        message=f"Failed to create collection '{self.mongo_collection}': {e}") from e

    def enable_sharding(self):
        shard_key = {"_id": 1}
        try:
            existing_shard_key = self.client.admin.command('shardCollection', f"{self.mongo_db}.{self.mongo_collection}")
            if existing_shard_key:
                logger.info(f"Collection '{self.mongo_collection}' is already sharded.")
            else:
                self.client.admin.command('shardCollection', f"{self.mongo_db}.{self.mongo_collection}", key=shard_key)
                logger.info(f"Sharding enabled for collection '{self.mongo_collection}' with shard key: {shard_key}.")
        except Exception as e:
            logger.error(f"Failed to enable sharding for collection '{self.mongo_collection}': {e}")
            raise MongoDBConnectorError(message=f"Failed to enable sharding: {e}") from e


class MongoConnectorRunner(MongoConnectorContextManager):
    def __init__(self, mongo_uri: str = MONGO_WRITER_URI, mongo_db: str = MONGO_DB,
                 mongo_collection: str = MONGO_COLLECTION) -> None:
        super().__init__(mongo_uri, mongo_db)
        self.mongo_collection = mongo_collection

    def __enter__(self):
        super().__enter__()
        if not DEBUG:
            self.ensure_non_admin_user()
        return self

    def upload_ocr_result(self, image_name: str, ocr_result: list[str], user_email: str) -> str:
        try:
            document_data = OCRedImageResult(
                user_email=user_email,
                filename=image_name,
                ocr_result=ocr_result
            )
            doc_to_insert = document_data.model_dump(by_alias=True)

            collection = self.database[self.mongo_collection]  # type: ignore[index]
            insert_result = collection.insert_one(doc_to_insert)
            inserted_id = insert_result.inserted_id

            logger.info(f"Successfully uploaded OCR result for '{image_name}' with id '{inserted_id}'.")
            return str(inserted_id)

        except Exception as e:
            logger.error(f"Failed to upload OCR result for '{image_name}': {e}")
            raise MongoDBConnectorError(message=f"Failed to upload OCR data: {e}") from e
