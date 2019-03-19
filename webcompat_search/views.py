import json
import os

from flask import Blueprint, url_for
from flask.json import jsonify

from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan as es_scan

from webcompat_search import settings


blueprint = Blueprint("domains", __name__)


@blueprint.route("/healthz", methods=["GET"])
def get_health():
    """Health check endpoint."""

    es = Elasticsearch([settings.ES_URL], **settings.ES_KWARGS)
    es_health = es.cluster.health()
    status_code = 200 if es_health["status"] == "green" else 500
    healthz = {"ES": es_health}

    return jsonify(healthz), status_code


@blueprint.route("/", methods=["GET"])
def get_schema():
    """API schema"""

    schema = {"search_by_domain": url_for(".get_domain", domain="_domain_")}
    return jsonify(schema)


@blueprint.route("/domain/<domain>")
def get_domain(domain):
    """Query for issues based on domain"""

    es = Elasticsearch([settings.ES_URL], **settings.ES_KWARGS)
    query = {"query": {"term": {"parsed_url.netloc.keyword": domain}}}

    results = es_scan(
        es,
        index=settings.ES_WEBCOMPAT_INDEX,
        query=query,
        scroll=settings.ES_SCROLL_LIMIT,
        size=settings.ES_QUERY_SIZE,
        preserve_order=True,
    )

    docs = []
    for result in results:
        docs.append(result["_source"])

    return jsonify(results=docs)


@blueprint.route("/dashboards/")
def get_dashboards():
    """Return list of available dashboards"""

    path = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(path, "fixtures/dashboards.json"), "r") as f:
        dashboards = json.load(f)

    return jsonify(dashboards)
