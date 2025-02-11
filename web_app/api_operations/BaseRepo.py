import logging
import os
from typing import Any, Dict, List, Optional, Type, TypeVar
from elasticsearch import Elasticsearch, NotFoundError, ElasticsearchException

T = TypeVar("T")

class BaseRepo:
    def __init__(self, index_name: str, es_client: Elasticsearch, klass: Type[T]):
        self.index_name = index_name.lower()
        self.es_client = es_client
        self.klass = klass
        self.logger = logging.getLogger(__name__)

    def query_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID."""
        try:
            response = self.es_client.get(index=self.index_name, id=doc_id)
            return response.get("_source", None)
        except NotFoundError:
            return None
        except ElasticsearchException as e:
            self.logger.error("Error retrieving document: %s", str(e))
            return None

    def create_index(self):
        """Create the index if it does not exist."""
        if not self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.create(index=self.index_name, body=self.index_settings())
            self.logger.info(f"Index '{self.index_name}' created!")

    def index_settings(self) -> Dict[str, Any]:
        """Define index settings and mappings."""
        return {
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {"properties": {"file_name": {"type": "text"}, "upload_time": {"type": "date"}, "content": {"type": "text"}}},
        }

    def delete_index(self):
        """Delete an index."""
        try:
            self.es_client.indices.delete(index=self.index_name)
        except ElasticsearchException as e:
            self.logger.error("Failed to delete index: %s", str(e))

    def clean_index(self):
        """Delete all documents from the index."""
        try:
            self.es_client.delete_by_query(index=self.index_name, body={"query": {"match_all": {}}})
        except ElasticsearchException as e:
            self.logger.error("Error cleaning index: %s", str(e))

    def query(self, query_str: str, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search documents using a query string."""
        body = {"query": {"match": {"content": query_str}}}
        if fields:
            body["_source"] = fields
        try:
            response = self.es_client.search(index=self.index_name, body=body)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except ElasticsearchException as e:
            self.logger.error("Error executing search query: %s", str(e))
            return []

    def bulk_index(self, docs: List[Dict[str, Any]]):
        """Bulk index multiple documents."""
        actions = [{"_index": self.index_name, "_source": doc} for doc in docs]
        try:
            self.es_client.bulk(index=self.index_name, body=actions)
        except ElasticsearchException as e:
            self.logger.error("Bulk indexing failed: %s", str(e))

    def delete_by_id(self, doc_id: str):
        """Delete a document by ID."""
        try:
            self.es_client.delete(index=self.index_name, id=doc_id)
        except ElasticsearchException as e:
            self.logger.error("Error deleting document: %s", str(e))

    def refresh_index(self):
        """Refresh the index to make all operations visible."""
        try:
            self.es_client.indices.refresh(index=self.index_name)
        except ElasticsearchException as e:
            self.logger.error("Error refreshing index: %s", str(e))
