from unittest.mock import MagicMock, patch

import pytest

from hydromosaic.database import Datafile, Model, Outlet, Scenario, Variable
from hydromosaic.indexing.index_netCDF import index_directory

MODULE = "hydromosaic.indexing.index_netCDF"


def make_model(id_=1):
    m = Model(short_name="test-model", institution="test-institution")
    m.id = id_
    return m


def make_scenario(id_=1):
    s = Scenario(short_name="historical", long_name="Historical")
    s.id = id_
    return s


def make_outlet(id_, code):
    o = Outlet(code=code)
    o.id = id_
    return o


def make_variable(id_, name):
    v = Variable(standard_name=name, long_name=name, units="1")
    v.id = id_
    return v


@pytest.fixture
def patched(monkeypatch):
    """Patch every collaborator index_directory calls, returning the mocks
    so each test can configure return values / side effects."""
    mocks = {}
    for name in [
        "create_engine",
        "sessionmaker",
        "Dataset",
        "get_model",
        "get_scenario",
        "get_outlets",
        "get_variables",
        "get_datafile",
        "get_timespan",
    ]:
        m = patch(f"{MODULE}.{name}").start()
        mocks[name] = m

    listdir = patch("os.listdir").start()
    mocks["listdir"] = listdir

    session = MagicMock()
    mocks["sessionmaker"].return_value.return_value = session
    mocks["session"] = session

    yield mocks

    patch.stopall()


def test_index_directory_indexes_single_file_and_builds_timeseries(patched):
    patched["listdir"].return_value = ["file1.nc"]
    patched["get_model"].return_value = make_model(id_=10)
    patched["get_scenario"].return_value = make_scenario(id_=20)
    patched["get_outlets"].return_value = [make_outlet(1, "A"), make_outlet(2, "B")]
    patched["get_variables"].return_value = [make_variable(1, "streamflow")]
    datafile = Datafile(filename="/some/dir/file1.nc")
    datafile.id = 99
    patched["get_datafile"].return_value = datafile
    patched["get_timespan"].return_value = ["2020-01-01", "2020-12-31", 366]

    index_directory(
        dsn="sqlite://", directory="/some/dir", log_level="info", gcm_prefix="p_"
    )

    # one Timeseries per (variable, outlet) pair -> 1 var * 2 outlets = 2
    added_timeseries = [
        c.args[0]
        for c in patched["session"].add.call_args_list
        if type(c.args[0]).__name__ == "Timeseries"
    ]
    assert len(added_timeseries) == 2
    assert {ts.outlet_id for ts in added_timeseries} == {1, 2}
    assert all(ts.variable_id == 1 for ts in added_timeseries)
    assert all(ts.model_id == 10 for ts in added_timeseries)
    assert all(ts.scenario_id == 20 for ts in added_timeseries)
    assert all(ts.datafile_id == 99 for ts in added_timeseries)

    patched["session"].commit.assert_called_once()
    patched["session"].close.assert_called_once()


def test_index_directory_builds_timeseries_for_every_variable_outlet_pair(patched):
    patched["listdir"].return_value = ["file1.nc"]
    patched["get_model"].return_value = make_model()
    patched["get_scenario"].return_value = make_scenario()
    patched["get_outlets"].return_value = [
        make_outlet(1, "A"),
        make_outlet(2, "B"),
        make_outlet(3, "C"),
    ]
    patched["get_variables"].return_value = [
        make_variable(1, "streamflow"),
        make_variable(2, "water_temp"),
    ]
    df = Datafile(filename="x")
    df.id = 1
    patched["get_datafile"].return_value = df
    patched["get_timespan"].return_value = ["2020-01-01", "2020-12-31", 366]

    index_directory(
        dsn="sqlite://", directory="/some/dir", log_level="info", gcm_prefix=""
    )

    added_timeseries = [
        c.args[0]
        for c in patched["session"].add.call_args_list
        if type(c.args[0]).__name__ == "Timeseries"
    ]
    # 3 outlets * 2 variables = 6
    assert len(added_timeseries) == 6


def test_index_directory_continues_after_one_file_fails(patched):
    patched["listdir"].return_value = ["bad.nc", "good.nc"]

    good_model = make_model(id_=1)
    good_scenario = make_scenario(id_=1)
    good_outlets = [make_outlet(1, "A")]
    good_variables = [make_variable(1, "streamflow")]
    good_datafile = Datafile(filename="good.nc")
    good_datafile.id = 5

    # Key get_model's failure off which file Dataset() was just called with,
    # since index_directory doesn't pass the filename to get_model directly.
    call_order = []

    def dataset_side_effect(path, mode):
        call_order.append(path)
        return MagicMock(name=path)

    patched["Dataset"].side_effect = dataset_side_effect

    def get_model_side_effect(nc, sesh, prefix):
        if call_order[-1].endswith("bad.nc"):
            raise Exception("Cannot determine model: no p_model_id attribute")
        return good_model

    patched["get_model"].side_effect = get_model_side_effect
    patched["get_scenario"].return_value = good_scenario
    patched["get_outlets"].return_value = good_outlets
    patched["get_variables"].return_value = good_variables
    patched["get_datafile"].return_value = good_datafile
    patched["get_timespan"].return_value = ["2020-01-01", "2020-12-31", 366]

    index_directory(
        dsn="sqlite://", directory="/some/dir", log_level="info", gcm_prefix="p_"
    )

    # commit still happens once at the end, even though one file failed
    patched["session"].commit.assert_called_once()

    added_timeseries = [
        c.args[0]
        for c in patched["session"].add.call_args_list
        if type(c.args[0]).__name__ == "Timeseries"
    ]
    # only the good file contributed a timeseries
    assert len(added_timeseries) == 1


def test_index_directory_rewrites_errno_51_to_readable_message(patched, caplog):
    patched["listdir"].return_value = ["notreallynetcdf.nc"]
    patched["Dataset"].side_effect = Exception(
        "[Errno -51] NetCDF: Unknown file format"
    )

    with caplog.at_level("ERROR"):
        index_directory(
            dsn="sqlite://", directory="/some/dir", log_level="info", gcm_prefix=""
        )

    assert any("Not a NetCDF file" in message for message in caplog.messages)
    assert not any("Errno -51" in message for message in caplog.messages)


def test_index_directory_passes_gcm_prefix_through(patched):
    patched["listdir"].return_value = ["file1.nc"]
    patched["get_model"].return_value = make_model(id_=1)
    patched["get_scenario"].return_value = make_scenario(id_=1)
    patched["get_outlets"].return_value = []
    patched["get_variables"].return_value = []
    df = Datafile(filename="file1.nc")
    df.id = 1
    patched["get_datafile"].return_value = df
    patched["get_timespan"].return_value = ["2020-01-01", "2020-12-31", 366]

    index_directory(
        dsn="sqlite://",
        directory="/some/dir",
        log_level="info",
        gcm_prefix="hydromodel__downscaling__GCM__",
    )

    model_call = patched["get_model"].call_args
    scenario_call = patched["get_scenario"].call_args
    assert model_call.args[2] == "hydromodel__downscaling__GCM__"
    assert scenario_call.args[2] == "hydromodel__downscaling__GCM__"


def test_index_directory_no_timeseries_when_no_outlets_or_variables(patched):
    patched["listdir"].return_value = ["file1.nc"]
    patched["get_model"].return_value = make_model(id_=1)
    patched["get_scenario"].return_value = make_scenario(id_=1)
    patched["get_outlets"].return_value = []
    patched["get_variables"].return_value = []
    df = Datafile(filename="file1.nc")
    df.id = 1
    patched["get_datafile"].return_value = df
    patched["get_timespan"].return_value = ["2020-01-01", "2020-12-31", 366]

    index_directory(
        dsn="sqlite://", directory="/some/dir", log_level="info", gcm_prefix=""
    )

    added_timeseries = [
        c.args[0]
        for c in patched["session"].add.call_args_list
        if type(c.args[0]).__name__ == "Timeseries"
    ]
    assert added_timeseries == []
    # the file with no variables/outlets is still considered indexed, not
    # a failure
    patched["session"].commit.assert_called_once()
