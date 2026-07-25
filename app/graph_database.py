from neo4j import Driver, GraphDatabase

from app.config import settings

_driver: Driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


def get_graph_driver() -> Driver:
    return _driver