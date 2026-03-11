"""Initial schema for market and politics modules."""

from __future__ import annotations

from alembic import op

from app.db.base import Base
from app.db.models import import_all_models


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    import_all_models()
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    import_all_models()
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
