# tests/test_database.py

from hydromosaic.database import (
    Base,
    Datafile,
    Model,
    Outlet,
    Scenario,
    Timeseries,
    Variable,
)


def test_expected_tables_exist():
    assert set(Base.metadata.tables) >= {
        "hydromosaic.outlets",
        "hydromosaic.variables",
        "hydromosaic.datafiles",
        "hydromosaic.models",
        "hydromosaic.scenarios",
        "hydromosaic.timeseries",
    }


def test_timeseries_foreign_keys():
    foreign_keys = {
        fk.target_fullname
        for column in Timeseries.__table__.columns
        for fk in column.foreign_keys
    }

    assert foreign_keys == {
        "hydromosaic.outlets.outlet_id",
        "hydromosaic.variables.variable_id",
        "hydromosaic.datafiles.datafile_id",
        "hydromosaic.models.model_id",
        "hydromosaic.scenarios.scenario_id",
    }
