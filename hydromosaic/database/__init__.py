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
    Date,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()
hm_schema = "hydromosaic"  # change if needed


class Outlet(Base):
    __tablename__ = "outlets"
    __table_args__ = {"schema": hm_schema}
    id = Column("outlet_id", Integer, primary_key=True)
    code = Column(String)


class Variable(Base):
    __tablename__ = "variables"
    __table_args__ = {"schema": hm_schema}
    id = Column("variable_id", Integer, primary_key=True)
    standard_name = Column(String)
    long_name = Column(String)
    units = Column(String)


class Datafile(Base):
    __tablename__ = "datafiles"
    __table_args__ = {"schema": hm_schema}
    id = Column("datafile_id", Integer, primary_key=True)
    filename = Column(String)
    index_time = Column(Date)


class Model(Base):
    __tablename__ = "models"
    __table_args__ = {"schema": hm_schema}
    id = Column("model_id", Integer, primary_key=True)
    long_name = Column(String)
    short_name = Column(String)
    institution = Column(String)


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = {"schema": hm_schema}
    id = Column("scenario_id", Integer, primary_key=True)
    long_name = Column(String)
    short_name = Column(String)


class Timeseries(Base):
    __tablename__ = "timeseries"
    __table_args__ = {"schema": hm_schema}
    id = Column("timeseries_id", Integer, primary_key=True)
    outlet_id = Column(Integer, ForeignKey("{}.outlets.outlet_id".format(hm_schema)))
    start_time = Column(Date)
    end_time = Column(Date)
    variable_id = Column(
        Integer, ForeignKey("{}.variables.variable_id".format(hm_schema))
    )
    datafile_id = Column(
        Integer, ForeignKey("{}.datafiles.datafile_id".format(hm_schema))
    )
    model_id = Column(Integer, ForeignKey("{}.models.model_id".format(hm_schema)))
    scenario_id = Column(
        Integer, ForeignKey("{}.scenarios.scenario_id".format(hm_schema))
    )
    num_times = Column(Integer)
