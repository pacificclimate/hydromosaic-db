import numpy
from psycopg2.extensions import register_adapter, AsIs


# Taken from https://github.com/pacificclimate/modelmeta/blob/924a25444ecca4dc283edb02507b18bdd08e8414/mm_cataloguer/psycopg2_adapters.py#L4
def register():
    """Register adapters for numpy types."""

    # Simple numeric types need only be converted by ``AsIs``
    for numpy_type in (
        numpy.int_,
        numpy.intc,
        numpy.intp,
        numpy.int8,
        numpy.int16,
        numpy.int32,
        numpy.int64,
        numpy.uint8,
        numpy.uint16,
        numpy.uint32,
        numpy.uint64,
        # numpy.float_, removed in the NumPy 2.0
        numpy.float16,
        numpy.float32,
        numpy.float64,
    ):
        register_adapter(numpy_type, AsIs)

    # Booleans have to be converted
    register_adapter(numpy.bool_, lambda v: AsIs(bool(v)))
