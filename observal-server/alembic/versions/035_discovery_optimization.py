# SPDX-FileCopyrightText: 2026 Observal Contributors
# SPDX-FileCopyrightText: 2026 Shaan Narendran <shaannaren06@gmail.com>
# SPDX-License-Identifier: Apache-2.0

"""Optional ARD discovery optimization in Insight reports.

Revision ID: 035_discovery_optimization
Revises: 034_hook_component_reports
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

from alembic import op

revision = "035_discovery_optimization"
down_revision = "034_hook_component_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "insight_reports",
        sa.Column("discovery_optimization_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("insight_reports", sa.Column("discovery_optimization", JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("insight_reports", "discovery_optimization")
    op.drop_column("insight_reports", "discovery_optimization_requested")
