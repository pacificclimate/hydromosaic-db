# accepts a directpry, adds metadata about each file in the directory to the database

import os
import logging
from netCDF4 import Dataset
from datetime import datetime, timedelta
from argparse import ArgumentParser
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hydromosaic.database import Outlet, Variable, Datafile, Model, Scenario, Timeseries


logger = logging.getLogger(__name__)


def get_outlets(nc, sesh):
    exception_prefix = "Cannot determine outlets: "
    if "nbasins" not in nc.dimensions:
        raise Exception(f"{exception_prefix}no nbasins dimension")
    if "basin_name" not in nc.variables:
        raise Exception(f"{exception_prefix}no basin_name variable")
    if len(nc.variables["basin_name"].dimensions) != 1:
        raise Exception(f"{exception_prefix}basin_name has wrong dimensionality")
    if "nbasins" not in nc.variables["basin_name"].dimensions:
        raise Exception(
            f"{exception_prefix}basin_name does not have an nbasins dimension"
        )

    outlets = []
    data = nc.variables["basin_name"][:].tolist()
    new_outlets = 0

    # TODO: maybe fetch all outlets at once and compare,
    # rather than making a call for each one?
    for out in data:
        outlet_match = sesh.query(Outlet).filter(Outlet.code == out).first()

        if outlet_match:
            outlets.append(outlet_match)
        else:
            new_outlets = new_outlets + 1
            o = Outlet(code=out)
            sesh.add(o)
            outlets.append(o)

    logger.info(f"{new_outlets} new outlets added to database")

    return outlets


def get_variables(nc, sesh):
    exception_prefix = "Cannot determine variables: "

    # variables we are able to construct a timeseries from must have
    # two dimesions, time and nbasins
    needed_dimensions = ["time", "nbasins"]
    for nd in needed_dimensions:
        if nd not in nc.dimensions:
            raise Exception(f"{exception_prefix}no {nd} dimension")

    variables = []
    new_vars = 0

    def timeseries_variable(var):
        if len(nc.variables[var].dimensions) != 2:
            return False
        for nd in needed_dimensions:
            if nd not in nc.variables[var].dimensions:
                return False
        return True

    for var in nc.variables:
        if timeseries_variable(var):
            if (
                "units" in nc.variables[var].ncattrs()
                and "long_name" in nc.variables[var].ncattrs()
            ):
                units = nc.variables[var].units
                long_name = nc.variables[var].long_name

                var_match = (
                    sesh.query(Variable).filter(Variable.standard_name == var).first()
                )
                if not var_match:
                    logger.info(f"variable {var} added to database")
                    new_vars = new_vars + 1
                    v = Variable(standard_name=var, long_name=long_name, units=units)
                    sesh.add(v)
                    variables.append(v)
                elif var_match.long_name == long_name and var_match.units == units:
                    variables.append(var_match)
                else:
                    raise Exception(
                        f"{exception_prefix}{var} already present in database with different metadata"
                    )
            else:
                logger.error(f"Could not parse variable {var}; attributes missing")

    logger.info(f"{len(variables)} timeseries variables found, {new_vars} newly added")
    return variables


def get_datafile(filename, sesh):
    file_match = sesh.query(Datafile).filter(Datafile.filename == filename).first()
    if file_match:
        raise Exception("This file has already been indexed")
    else:
        d = Datafile(filename=filename, index_time=datetime.now())
        sesh.add(d)
        return d


def get_timespan(nc):
    exception_prefix = "Cannot determine timespan: "
    if "time" not in nc.variables:
        raise Exception(f"{exception_prefix}no time variable")
    if "units" not in nc.variables["time"].ncattrs():
        raise Exception(f"{exception_prefix}time has no units")
    if not nc.variables["time"].units.startswith("hours since "):
        raise Exception(f"{exception_prefix}cannot parse time units")

    ref_time_str = nc.variables["time"].units.split("since ")[1]
    try:
        reference_date = datetime.strptime(ref_time_str, "%Y-%m-%d %H:%M:%S").date()
    except:
        raise Exception(f"{exception_prefix}could not parse reference {ref_time_str}")

    time_data = nc.variables["time"][:]

    return [
        reference_date + timedelta(hours=time_data[0]),
        reference_date + timedelta(hours=time_data[-1]),
        len(time_data),
    ]


# TODO: genericize object attributes across model and scenario
def get_model(nc, sesh, gcm_prefix):
    exception_prefix = "Cannot determine model: "
    model_attribute = f"{gcm_prefix}model_id"
    institute_attribute = f"{gcm_prefix}institute_id"
    file_attrs = nc.ncattrs()

    for needed in [institute_attribute, model_attribute]:
        if not f"{needed}" in file_attrs:
            raise Exception(f"{exception_prefix}no {needed} attribute")

    model_name = nc.getncattr(model_attribute)
    model_institution = nc.getncattr(institute_attribute)

    # if we have no model with this model_id, add a new one
    # if we have a model with this model_id but a different institute, raise an error
    # if we have a model with this model id and this institute, use that one
    model_match = sesh.query(Model).filter(Model.short_name == model_name).first()

    if not model_match:
        logger.info(f"{model_name} model added to database")
        m = Model(short_name=model_name, institution=model_institution)
        sesh.add(m)
        return m
    elif model_match.institution == model_institution:
        return model_match
    else:
        raise Exception(
            f"{exception_prefix}{model_name} exists with institution {model_match.institution}, but the file uses {model_institution}"
        )


def get_scenario(nc, sesh, gcm_prefix):
    exception_prefix = "Cannot determine scenario: "
    short_attribute = f"{gcm_prefix}experiment_id"
    long_attribute = f"{gcm_prefix}experiment"
    file_attrs = nc.ncattrs()

    for needed in [short_attribute, long_attribute]:
        if not f"{needed}" in file_attrs:
            raise Exception(f"{exception_prefix}no {needed} attribute")

    scenario_short = nc.getncattr(short_attribute)
    scenario_long = nc.getncattr(long_attribute)

    # if we have no scenario with this scenario_id, add a new one
    # if we have a scenario with this scenario_id but a different long name, raise an error
    # if we have a scenario with this scenario id and this long name, use that one
    scenario_match = (
        sesh.query(Scenario).filter(Scenario.short_name == scenario_short).first()
    )

    if not scenario_match:
        logger.info(f"{scenario_short} scenario added to database")
        s = Scenario(short_name=scenario_short, long_name=scenario_long)
        sesh.add(s)
        return s
    elif scenario_match.long_name == scenario_long:
        return scenario_match
    else:
        raise Exception(
            f"{exception_prefix}{scenario_short} exists with long name {scenario_match.long_name}, but the file uses {scenario_long}"
        )


def index_directory(dsn, directory, log_level, gcm_prefix):
    engine = create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    log_levels = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    logging.basicConfig(level=log_levels[log_level])

    unindexable = {}
    indexed = []
    num_timeseries = 0

    for file in os.listdir(directory):
        logger.info(f"Now indexing {file}")
        try:
            nc = Dataset(f"{directory}/{file}", "r")

            # database objects derived from nc file attributes
            model = get_model(nc, session, gcm_prefix)
            scenario = get_scenario(nc, session, gcm_prefix)

            # database objects derived from nc file data
            outlets = get_outlets(nc, session)
            variables = get_variables(nc, session)
            datafile = get_datafile(os.path.abspath(f"{directory.rstrip('/')}/{file}"), session)
            start, end, num_times = get_timespan(nc)

            # flush objects so that they get primary keys assigned before
            # we create the timeseries entry
            session.flush()

            for variable in variables:
                for outlet in outlets:
                    ts = Timeseries(
                        outlet_id=outlet.id,
                        variable_id=variable.id,
                        datafile_id=datafile.id,
                        model_id=model.id,
                        scenario_id=scenario.id,
                        start_time=start,
                        end_time=end,
                        num_times=num_times,
                    )
                    session.add(ts)
                    num_timeseries = num_timeseries + 1
            indexed.append(file)

        except Exception as e:
            message = str(e)
            # make a couple errors more readable
            if message.startswith("[Errno -51]"):
                message = "Not a NetCDF file"
            unindexable[file] = message

    session.commit()
    session.close()
    logger.info(
        f"Successfully indexed {len(indexed)} files and {num_timeseries} timeseries."
    )
    for file in indexed:
        logger.debug("{} was indexed".format(file))
    logger.error("The following files could not be indexed:")
    for file in unindexable:
        logger.error(f"{file}: {unindexable[file]}")
