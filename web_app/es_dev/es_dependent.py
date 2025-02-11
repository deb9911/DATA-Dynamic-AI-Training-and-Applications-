import os
from elasticsearch import Elasticsearch


def create_ES_index(es):
    index_name = "datasets"

    # Check if the index exists; if not, create it
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            "mappings": {
                "properties": {
                    "file_name": {"type": "text"},
                    "upload_time": {"type": "date"},
                    "content": {"type": "text"}
                }
            }
        })
        print(f"Index '{index_name}' created!")
        return index_name

