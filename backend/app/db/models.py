from app import models  # noqa: F401
from app.politics import models as political_models  # noqa: F401


def import_all_models() -> None:
    """Import modules so SQLAlchemy metadata is populated for Alembic and tests."""
