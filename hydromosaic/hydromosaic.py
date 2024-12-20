from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    Boolean,
    Float,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()
hm_schema = "hydro_geometry"  # change if needed

class Outlet(Base):
    __tablename__ = "outlets"
    __table_args__ = {"schema": hm_schema}
    id = Column("outlet_id", Integer, primary_key=True)
    code = Column(String)

    
class Feature(Base):
    """Base type for features. Features need to be polymorphic because
    rivers are polylines, but basins and lakes are polygons"""
    __tablename__ = "features"
    __table_args__ = {"schema": hm_schema}
    id = Column("feature_id", Integer, primary_key=True)
    outlet_id = Column(Integer, ForeignKey("{}.outlet.outlet_id".format(hm_schema)))
    downstream_outlet_id = Column(Integer, ForeignKey("{}.outlet.outlet_id".format(hm_schema)))
    featureType=Column(Enum("basin", "lake", "river", name="featureType"), nullable=False)
    
    __mapper_args__ = {
        "polymorphic_identity": "features",
        "polymorphic_on": featureType,
    }
    
class Basin(Feature):
    __tablename__ = "basins"
    __table_args__ = {"schema": hm_schema}
    id = Column("basin_id", Integer, ForeignKey("{}.features.feature_id".format(hm_schema)), primary_key=True)
    geometry = Colum(Geometry("POLYGON"))
    
    __mapper_args__ = {"polymorphic_identity": "basin"}
    
    
class River(Feature):
    __tablename__ = "rivers"
    __table_args__ = {"schema": hm_schema}
    id = Column("river_id", Integer, ForeignKey("{}.features.feature_id".format(hm_schema)), primary_key=True)
    geometry = Colum(Geometry("POLYLINE"))
    
    __mapper_args__ = {"polymorphic_identity": "river"}


class Lake(Feature):
    __tablename__ = "lakes"
    __table_args__ = {"schema": hm_schema}
    id = Column("lake_id", Integer, ForeignKey("{}.features.feature_id".format(hm_schema)), primary_key=True)
    geometry = Colum(Geometry("POLYGON"))
    
    __mapper_args__ = {"polymorphic_identity": "lake"}

    
class Variable(Base):
    __tablename__ = "variables"
    __table_args__ = {"schema": hm_schema}
    id = Column("variable_id", Integer, primary_key=True)
    standard_name = Column(String)
    long_name = Column(String)
    units = Column(String)

    
class Time(Base):
    __tablename__ = "times"
    __table_args__ = {"schema": hm_schema}
    id = Column("time_id", Integer, primary_key=True)
    time = Column(Date)


class Datafile(Base):
    __tablename__ = "data_files"
    __table_args__ = {"schema": hm_schema}
    id = Column("data_file_id", Integer, primary_key=True)
    filename=Column(String)
    index_time=Column(Date)
    
class Model(Base):
    __tablename__ = "models"
    __table_args__ = {"schema": hm_schema}
    id = Column("models_id", Integer, primary_key=True)
    long_name=Column(String)
    short_name=Column(String)
    

class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = {"schema": hm_schema}
    id = Column("scenarios_id", Integer, primary_key=True)
    long_name=Column(String)
    short_name=Column(String)


class Timeseries(Base):
    __tablename__ = "timeseries"
    __table_args__ = {"schema": hm_schema}
    id = Column("timeseries_id", Integer, primary_key=True)
    outlet_id = Column(Integer, ForeignKey("{}.outlets.outlet_id".format(hm_schema)))
    start_time = Column(Integer, ForeignKey("{}.times.time_id".format(hm_schema)))
    end_time = Column(Integer, ForeignKey("{}.times.time_id".format(hm_schema)))
    variable_id = Column(Integer, ForeignKey("{}.variables.variable_id".format(hm_schema)))
    datafile_id = Column(Integer, ForeignKey("{}.datafiles.datafile_id".format(hm_schema)))
    model_id = Column(Integer, ForeignKey("{}.models.model_id".format(hm_schema)))
    scenario_id = Column(Integer, ForeignKey("{}.scenarios.scenario_id".format(hm_schema)))
    num_times = Column(Integer)
    
    