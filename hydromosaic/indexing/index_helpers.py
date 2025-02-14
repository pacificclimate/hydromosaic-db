"""Database utility functions for indexer"""


def find(sesh, Thing, attributes):
    """Find an existing database Thing matching the given attributes."""
    query = sesh.query(Thing).filter_by(**attributes)
    return query.first()


def insert(sesh, Thing, attributes):
    """Insert a new database Thing with given attributes."""
    thing = Thing(**attributes)
    sesh.add(thing)
    return thing


def find_or_insert(sesh, Thing, find_attrs, insert_attrs):
    """Find or insert a database Thing with given attributes.
    Since the attributes for finding are typically a subset of those for inserting,
    the two sets of attributes are separate arguments, merged for insert.
    """
    return find(sesh, Thing, find_attrs) or insert(
        sesh, Thing, {**find_attrs, **insert_attrs}
    )