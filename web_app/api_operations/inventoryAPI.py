from flask import Flask, request, jsonify, Response
from elasticsearch import Elasticsearch
import logging
import json
from datetime import datetime
import pytz

app = Flask(__name__)
es = Elasticsearch("http://localhost:9200")  # Update Elasticsearch connection if required

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Dummy IndexManager class for handling Elasticsearch operations (to be implemented)
class IndexManager:
    def __init__(self):
        pass

    def node_repository(self, customer):
        return NodeRepository(customer)

    def itsm_repository(self, customer, model):
        return ITSMRepository(customer, model)

    def alarm_repository(self, customer):
        return AlarmRepository(customer)


index_manager = IndexManager()


# ----------------------------- Endpoints -----------------------------

@app.route("/api/inventory/<customer>/summary", methods=["POST"])
def get_summary(customer):
    """Returns inventory summary with vendor and subtype aggregation."""
    query_request = request.get_json()

    summary = {}
    node_repo = index_manager.node_repository(customer)

    query = {
        "size": 0,
        "aggs": {
            "filter": {
                "filter": {
                    "bool": query_request.get("filter", {})
                },
                "aggs": {
                    "vendor": {
                        "multi_terms": {
                            "terms": [
                                {"field": "oem"},
                                {"field": "subtype"}
                            ],
                            "size": 1000
                        }
                    }
                }
            }
        }
    }

    response = es.search(index="nodes_index", body=query)
    vendor_buckets = response["aggregations"]["filter"]["vendor"]["buckets"]

    for bucket in vendor_buckets:
        vendor = bucket["key"][0]
        subtype = bucket["key"][1]
        count = bucket["doc_count"]

        if vendor not in summary:
            summary[vendor] = {}

        summary[vendor][subtype] = count

    return jsonify(summary)


@app.route("/api/inventory/<customer>/list", methods=["POST"])
def get_inventory(customer):
    """Returns paginated inventory details."""
    query_request = request.get_json()
    page = query_request.get("page", 1)
    size = query_request.get("size", 10)

    if page < 1 or size < 1:
        return jsonify({"error": "Page and size should be greater than 0"}), 400

    from_ = (page - 1) * size

    query = {
        "from": from_,
        "size": size,
        "query": query_request.get("filter", {}),
        "sort": query_request.get("sort_by", [])
    }

    response = es.search(index="nodes_index", body=query)
    results = [hit["_source"] for hit in response["hits"]["hits"]]

    return jsonify({
        "total": response["hits"]["total"]["value"],
        "items": results
    })


@app.route("/api/inventory/<customer>/export", methods=["POST"])
def export_inventory(customer):
    """Exports inventory data as a downloadable file."""
    query_request = request.get_json()
    query = {
        "query": query_request.get("filter", {}),
        "sort": query_request.get("sort_by", [])
    }

    response = es.search(index="nodes_index", body=query, size=10000)  # Exporting all records

    filename = f"inventory_export_{customer}.json"
    export_data = json.dumps([hit["_source"] for hit in response["hits"]["hits"]], indent=2)

    return Response(
        export_data,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/inventory/<customer>/<node_id>", methods=["GET"])
def get_inventory_item_details(customer, node_id):
    """Fetches details of a specific inventory item by node ID."""
    response = es.get(index="nodes_index", id=node_id, ignore=[404])

    if not response.get("found", False):
        return jsonify({"error": "Node with provided id doesn't exist"}), 404

    node_data = response["_source"]

    result = {
        "name": node_data.get("name"),
        "status": node_data.get("status"),
        "vendor": node_data.get("vendor"),
        "oem": node_data.get("oem"),
        "type": node_data.get("type"),
        "site": node_data.get("site"),
        "subtype": node_data.get("subtype"),
        "region": node_data.get("region"),
        "cloud_node": node_data.get("cloud_node"),
        "physical": node_data.get("physical"),
        "attributes": format_attributes(node_data.get("attributes", [])),
        "alarms": get_alarms(customer, node_id),
        "incidents": get_incidents(customer, node_id),
        "changes": get_change_requests(customer, node_id)
    }

    return jsonify(result)


# ----------------------------- Helper Functions -----------------------------

def format_attributes(attributes):
    """Formats attributes, particularly LAST_MODIFIED_ON."""
    for attr in attributes:
        if attr["name"] == "LAST_MODIFIED_ON":
            try:
                attr["value"] = format_datetime(float(attr["value"]) * 1000)
            except ValueError:
                logger.debug(f"Cannot parse LAST_MODIFIED_ON field with value {attr['value']}")
    return attributes


def format_datetime(timestamp, timezone="UTC"):
    """Formats timestamp into readable datetime format."""
    tz = pytz.timezone(timezone)
    return datetime.fromtimestamp(timestamp / 1000, tz).strftime("%Y-%m-%d %H:%M:%S")


def get_alarms(customer, node_id):
    """Fetches aggregated alarms for a node."""
    query = {
        "query": {"match": {"node_id": node_id}},
        "aggs": {"severity": {"terms": {"field": "severity"}}},
        "size": 0
    }

    response = es.search(index="alarms_index", body=query)
    return response["aggregations"]["severity"]["buckets"] if "aggregations" in response else {}


def get_incidents(customer, node_id):
    """Fetches incidents linked to a node."""
    query = {
        "query": {"match": {"node_id": node_id}},
        "aggs": {"priority": {"terms": {"field": "priority"}}},
        "size": 0
    }

    response = es.search(index="incidents_index", body=query)
    return response["aggregations"]["priority"]["buckets"] if "aggregations" in response else {}


def get_change_requests(customer, node_id):
    """Fetches change requests linked to a node."""
    query = {
        "query": {"match": {"node_id": node_id}},
        "aggs": {"status": {"terms": {"field": "status"}}},
        "size": 0
    }

    response = es.search(index="change_requests_index", body=query)
    return response["aggregations"]["status"]["buckets"] if "aggregations" in response else {}


# ----------------------------- Supporting Classes -----------------------------

class NodeRepository:
    """Placeholder class for handling node repository operations."""

    def __init__(self, customer):
        self.customer = customer

    def paging(self, filter_query, sort_by, from_, size):
        return es.search(index="nodes_index",
                         body={"query": filter_query, "sort": sort_by, "from": from_, "size": size})


class ITSMRepository:
    """Placeholder class for handling ITSM (Incidents/Changes)."""

    def __init__(self, customer, model):
        self.customer = customer
        self.model = model

    def aggregates_change_requests_by_severity(self, node_set, from_time, to_time):
        return {}


class AlarmRepository:
    """Placeholder class for handling Alarm operations."""

    def __init__(self, customer):
        self.customer = customer

    def aggregates_severity_for_nodes(self, node_set, from_time, to_time):
        return {}


# ----------------------------- Run Server -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
