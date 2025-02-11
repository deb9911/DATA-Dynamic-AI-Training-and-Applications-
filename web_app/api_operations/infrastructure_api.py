from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
from datetime import datetime
from collections import defaultdict
import logging

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")  # Update with actual Elasticsearch URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/api/infra/<customer>/regions", methods=["GET"])
def get_regions(customer):
    query = {
        "query": {"match": {"customer": customer}},
        "_source": ["region", "name", "site", "subtype", "id"],
        "size": 10000
    }

    response = es.search(index="sites", body=query)
    regions = defaultdict(list)
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        regions[source["region"]].append({
            "id": source["id"],
            "name": source["name"],
            "subtype": source["subtype"],
        })

    return jsonify([{"region": key, "sites": value} for key, value in regions.items()])


@app.route("/api/infra/<customer>/types", methods=["GET"])
def get_types(customer):
    query = {
        "size": 0,
        "aggs": {
            "types": {"terms": {"field": "type.keyword", "size": 10000}}
        }
    }
    response = es.search(index="nodes", body=query)
    types = {bucket["key"] for bucket in response["aggregations"]["types"]["buckets"]}
    types.update({"router", "vdc", "vm", "csu", "switch", "vnf"})
    return jsonify(list(types))


@app.route("/api/infra/<customer>/subtypes", methods=["GET"])
def get_subtypes(customer):
    query = {
        "size": 0,
        "aggs": {
            "subtypes": {"terms": {"field": "subtype.keyword", "size": 10000}}
        }
    }
    response = es.search(index="nodes", body=query)
    subtypes = {bucket["key"] for bucket in response["aggregations"]["subtypes"]["buckets"]}
    subtypes.update({"router", "vdc", "vm", "csu", "switch", "vnf"})
    return jsonify(list(subtypes))


@app.route("/api/infra/<customer>/nodes", methods=["GET"])
def get_nodes(customer):
    filter_query = request.args.get("filter", "")
    query = {"query": {"match": {"customer": customer}}, "size": 10000}
    if filter_query:
        query["query"] = {"query_string": {"query": filter_query}}
    response = es.search(index="nodes", body=query)
    return jsonify([hit["_source"] for hit in response["hits"]["hits"]])


@app.route("/api/infra/<customer>/aggregate", methods=["GET"])
def get_aggregate(customer):
    query = {
        "size": 10000,
        "query": {"match": {"customer": customer}},
        "_source": ["name", "vendor"]
    }
    response = es.search(index="nodes", body=query)
    aggregation = defaultdict(list)
    for hit in response["hits"]["hits"]:
        source = hit["_source"]
        vendor = source.get("vendor", "Unknown")
        aggregation[vendor].append(source)
    return jsonify(aggregation)


@app.route("/api/infra/<customer>/network/<ids>", methods=["GET"])
def query_network(customer, ids):
    root_ids = ids.split(",")
    query = {
        "query": {"ids": {"values": root_ids}},
        "size": 10000
    }
    response = es.search(index="nodes", body=query)
    nodes = [hit["_source"] for hit in response["hits"]["hits"]]

    if not nodes:
        return jsonify({"error": "No nodes found"}), 404

    return jsonify(nodes)


if __name__ == "__main__":
    app.run(debug=True)
