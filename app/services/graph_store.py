import uuid

from neo4j import Driver

from app.graph_database import get_graph_driver


def store_chunk_graph(
    driver: Driver, document_id: uuid.UUID, chunk_id: uuid.UUID, extraction: dict
) -> None:
    """
    Write extracted entities and relationships into Neo4j, tagging each entity
    with which chunk and document it came from, so graph traversal can be
    linked back to real chunk content later.
    """
    entities = extraction.get("entities", [])
    relationships = extraction.get("relationships", [])

    with driver.session() as session:
        for entity in entities:
            session.run(
                """
                MERGE (e:Entity {name: $name})
                SET e.type = $type
                MERGE (c:Chunk {id: $chunk_id})
                SET c.document_id = $document_id
                MERGE (e)-[:MENTIONED_IN]->(c)
                """,
                name=entity["name"],
                type=entity.get("type", "Unknown"),
                chunk_id=str(chunk_id),
                document_id=str(document_id),
            )

        for rel in relationships:
            session.run(
                """
                MERGE (source:Entity {name: $source})
                MERGE (target:Entity {name: $target})
                MERGE (source)-[r:RELATES_TO {type: $rel_type}]->(target)
                """,
                source=rel["source"],
                target=rel["target"],
                rel_type=rel.get("type", "RELATED_TO"),
            )