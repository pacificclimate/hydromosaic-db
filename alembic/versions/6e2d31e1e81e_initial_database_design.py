"""initial database design

Revision ID: 6e2d31e1e81e
Revises: 
Create Date: 2025-01-16 20:19:56.436403

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '6e2d31e1e81e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

schema_name = "hydromosaic"

def upgrade():
    op.create_table(
        "outlets",
        sa.Column("outlet_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("outlet_id"),
        schema = schema_name
        )
    
    op.create_table(
        "variables",
        sa.Column("variable_id", sa.Integer(), nullable = False),
        sa.Column("standard_name", sa.String(), nullable = False),
        sa.Column("long_name", sa.String()),
        sa.Column("units", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("variable_id"),
        schema = schema_name
        )

    
    op.create_table(
        "datafiles",
        sa.Column("datafile_id", sa.Integer(), nullable = False),
        sa.Column("filename", sa.String(), nullable = False),
        sa.Column("index_time", sa.Date()),
        sa.PrimaryKeyConstraint("datafile_id"),
        schema = schema_name,
        )

    op.create_table(
        "models",
        sa.Column("model_id", sa.Integer(), nullable = False), 
        sa.Column("long_name", sa.String()),
        sa.Column("short_name", sa.String(), nullable = False),
        sa.Column("institution", sa.String()),
        sa.PrimaryKeyConstraint("model_id"),
        schema = schema_name
        )

    op.create_table(
        "scenarios",
        sa.Column("scenario_id", sa.Integer(), nullable = False),
        sa.Column("long_name", sa.String()),
        sa.Column("short_name", sa.String, nullable = False),
        sa.PrimaryKeyConstraint("scenario_id"),
        schema = schema_name
        )


    op.create_table(
        "timeseries",
        sa.Column("timeseries_id", sa.Integer(), nullable = False),
        sa.Column("outlet_id", sa.Integer(), nullable = False),
        sa.Column("start_time", sa.Date(), nullable = False),
        sa.Column("end_time", sa.Date(), nullable = False),
        sa.Column("variable_id", sa.Integer(), nullable = False),
        sa.Column("datafile_id", sa.Integer(), nullable = False),
        sa.Column("model_id", sa.Integer(), nullable = False),
        sa.Column("scenario_id", sa.Integer(), nullable = False),
        sa.Column("num_times", sa.Integer(), nullable = False),
        sa.PrimaryKeyConstraint("timeseries_id"),
        sa.ForeignKeyConstraint(["outlet_id"], [f"{schema_name}.outlets.outlet_id"]),
        sa.ForeignKeyConstraint(["variable_id"], [f"{schema_name}.variables.variable_id"]),
        sa.ForeignKeyConstraint(["datafile_id"], [f"{schema_name}.datafiles.datafile_id"]),
        sa.ForeignKeyConstraint(["model_id"], [f"{schema_name}.models.model_id"]),
        sa.ForeignKeyConstraint(["scenario_id"], [f"{schema_name}.scenarios.scenario_id"]),
        )


def downgrade():
        op.drop_table("timeseries", schema=schema_name)
        op.drop_table("scenarios", schema=schema_name)
        op.drop_table("models", schema=schema_name)
        op.drop_table("datafiles", schema=schema_name)
        op.drop_table("times", schema=schema_name)
        op.drop_table("variables", schema=schema_name)
        op.drop_table("outlets", schema=schema_name)
