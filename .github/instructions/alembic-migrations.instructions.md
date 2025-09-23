---
applyTo: "migrations/versions/*.py"
---
## Alembic Migrations

### Data Migrations

For migrations that include data mutation, and not only schema modifications, use this pattern to setup a session:

```python
from alembic import op
from sqlmodel import Session
from activemodel.session_manager import global_session
from app import log

def run_migration_helper():
  pass

def upgrade() -> None:
  session = Session(bind=op.get_bind())

  with global_session(session):
      run_migration_helper()
      flip_point_coordinates()
      backfill_screening_host_data()

  # flush before running any other operations, otherwise not all changes will persist to the transaction
  session.flush()
```
