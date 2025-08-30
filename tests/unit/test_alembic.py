"""
https://medium.com/exness-blog/alembic-migrations-without-downtime-a3507d5da24d
"""

from alembic.config import Config
from alembic.script import ScriptDirectory

from app.setup import get_root_path


def test_only_single_head_revision_in_migrations():
    alembic_cfg = Config(get_root_path() / "alembic.ini")
    alembic_cfg.set_main_option("skip_logging_config", "true")
    script = ScriptDirectory.from_config(alembic_cfg)

    # This will raise if there are multiple heads
    script.get_current_head()
