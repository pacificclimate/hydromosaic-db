from unittest.mock import MagicMock

import pytest

from hydromosaic.database import Model, Scenario
from hydromosaic.indexing.index_netCDF import get_model, get_scenario


GCM_PREFIX = "hydromodel__downscaling__GCM__"
OBS_PREFIX = "hydromodel__observations__"


def mock_query_result(session, result):
    query = MagicMock()
    query.filter.return_value.first.return_value = result
    session.query.return_value = query


def make_nc(attrs):
    nc = MagicMock()
    nc.ncattrs.return_value = list(attrs.keys())
    nc.getncattr.side_effect = lambda name: attrs[name]
    return nc


# ---------------------------------------------------------------------------
# get_model
# ---------------------------------------------------------------------------


def test_get_model_creates_cmip6_model_with_gcm_prefix():
    nc = make_nc(
        {
            "project_id": "CMIP6",
            f"{GCM_PREFIX}model_id": "CNRM-ESM2-1",
            f"{GCM_PREFIX}institution_id": "CNRM-CERFACS",
        }
    )

    session = MagicMock()
    mock_query_result(session, None)

    result = get_model(nc, session, GCM_PREFIX)

    assert result.short_name == "CNRM-ESM2-1"
    assert result.institution == "CNRM-CERFACS"
    session.add.assert_called_once()


def test_get_model_reuses_existing_model_with_gcm_prefix():
    nc = make_nc(
        {
            "project_id": "CMIP6",
            f"{GCM_PREFIX}model_id": "CNRM-ESM2-1",
            f"{GCM_PREFIX}institution_id": "CNRM-CERFACS",
        }
    )

    existing = Model(short_name="CNRM-ESM2-1", institution="CNRM-CERFACS")

    session = MagicMock()
    mock_query_result(session, existing)

    result = get_model(nc, session, GCM_PREFIX)

    assert result is existing
    session.add.assert_not_called()


def test_get_model_rejects_conflicting_institution_with_gcm_prefix():
    nc = make_nc(
        {
            "project_id": "CMIP6",
            f"{GCM_PREFIX}model_id": "CNRM-ESM2-1",
            f"{GCM_PREFIX}institution_id": "CNRM-CERFACS",
        }
    )

    existing = Model(short_name="CNRM-ESM2-1", institution="SOME-OTHER-INSTITUTION")

    session = MagicMock()
    mock_query_result(session, existing)

    with pytest.raises(Exception, match="exists with institution"):
        get_model(nc, session, GCM_PREFIX)


def test_get_model_wrong_prefix_raises_clear_error():
    nc = make_nc(
        {
            "project_id": "CMIP6",
            f"{GCM_PREFIX}model_id": "CNRM-ESM2-1",
            f"{GCM_PREFIX}institution_id": "CNRM-CERFACS",
        }
    )

    session = MagicMock()

    with pytest.raises(Exception, match="no hydromodel__observations__institution_id attribute"):
        get_model(nc, session, OBS_PREFIX)


def test_get_model_uses_institute_id_for_non_cmip6():
    nc = make_nc(
        {
            "project_id": "CMIP5",
            f"{GCM_PREFIX}model_id": "CanESM2",
            f"{GCM_PREFIX}institute_id": "CCCma",
        }
    )

    session = MagicMock()
    mock_query_result(session, None)

    result = get_model(nc, session, GCM_PREFIX)

    assert result.short_name == "CanESM2"
    assert result.institution == "CCCma"


# ---------------------------------------------------------------------------
# get_scenario
# ---------------------------------------------------------------------------


def test_get_scenario_creates_new_scenario_future_file():
    nc = make_nc(
        {
            f"{GCM_PREFIX}experiment_id": "historical, ssp245",
            f"{GCM_PREFIX}experiment": "Historical + Representative Concentration Pathway 45",
        }
    )

    session = MagicMock()
    mock_query_result(session, None)

    result = get_scenario(nc, session, GCM_PREFIX)

    assert result.short_name == "historical, ssp245"
    assert result.long_name == "Historical + Representative Concentration Pathway 45"
    session.add.assert_called_once()


def test_get_scenario_creates_new_scenario_historical_file():
    nc = make_nc(
        {
            f"{OBS_PREFIX}experiment_id": "historical",
            f"{OBS_PREFIX}experiment": "historical observations",
        }
    )

    session = MagicMock()
    mock_query_result(session, None)

    result = get_scenario(nc, session, OBS_PREFIX)

    assert result.short_name == "historical"
    assert result.long_name == "historical observations"
    session.add.assert_called_once()


def test_get_scenario_reuses_existing_scenario_with_prefix():
    nc = make_nc(
        {
            f"{OBS_PREFIX}experiment_id": "historical",
            f"{OBS_PREFIX}experiment": "historical observations",
        }
    )

    existing = Scenario(short_name="historical", long_name="historical observations")

    session = MagicMock()
    mock_query_result(session, existing)

    result = get_scenario(nc, session, OBS_PREFIX)

    assert result is existing
    session.add.assert_not_called()


def test_get_scenario_rejects_conflicting_metadata_with_prefix():
    nc = make_nc(
        {
            f"{OBS_PREFIX}experiment_id": "historical",
            f"{OBS_PREFIX}experiment": "a different long name",
        }
    )

    existing = Scenario(short_name="historical", long_name="historical observations")

    session = MagicMock()
    mock_query_result(session, existing)

    with pytest.raises(Exception, match="exists with long name"):
        get_scenario(nc, session, OBS_PREFIX)


def test_get_scenario_wrong_prefix_raises_clear_error():
    nc = make_nc(
        {
            f"{GCM_PREFIX}experiment_id": "historical, ssp245",
            f"{GCM_PREFIX}experiment": "Historical + Representative Concentration Pathway 45",
        }
    )

    session = MagicMock()

    with pytest.raises(Exception, match=f"no {OBS_PREFIX}experiment_id attribute"):
        get_scenario(nc, session, OBS_PREFIX)