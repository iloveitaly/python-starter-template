"""Add typeid_parse and base32_decode functions

Helpful when writing SQL queries directly vs using sqlalchemy.

Revision ID: 489aff797e2e
Revises: 729942e5417d
Create Date: 2025-03-27 20:02:44.254927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import activemodel


# revision identifiers, used by Alembic.
revision: str = '489aff797e2e'
down_revision: Union[str, None] = '729942e5417d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    "https://github.com/jetify-com/typeid-sql/blob/main/sql/02_base32.sql"

    op.execute("""
CREATE OR REPLACE FUNCTION typeid_parse(typeid_str text)
        RETURNS uuid
        AS $$
        DECLARE
          prefix text;
          suffix text;
        BEGIN
          IF (typeid_str IS NULL) THEN
            RETURN NULL;
          END IF;
          IF POSITION('_' IN typeid_str) = 0 THEN
            RETURN base32_decode(typeid_str)::uuid;
          END IF;
          prefix := SPLIT_PART(typeid_str, '_', 1);
          suffix := SPLIT_PART(typeid_str, '_', 2);
          IF prefix IS NULL OR prefix = '' THEN
            RAISE EXCEPTION 'typeid prefix cannot be empty with a delimiter';
          END IF;
          IF NOT prefix ~ '^[a-z]{1,63}$' THEN
            RAISE EXCEPTION 'typeid prefix must match the regular expression [a-z]{1,63}';
          END IF;
          RETURN base32_decode(suffix)::uuid;
        END
        $$
        LANGUAGE plpgsql
        IMMUTABLE;

create or replace function base32_decode(s text)
returns uuid as $$
declare
  dec bytea = '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF 00 01'::bytea ||
              '\x02 03 04 05 06 07 08 09 FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF 0A 0B 0C'::bytea ||
              '\x0D 0E 0F 10 11 FF 12 13 FF 14'::bytea ||
              '\x15 FF 16 17 18 19 1A FF 1B 1C'::bytea ||
              '\x1D 1E 1F FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\xFF FF FF FF FF FF'::bytea;
  v bytea = convert_to(s, 'UTF8');
  id bytea = '\x00000000000000000000000000000000';
begin
  if length(s) <> 26 then
    raise exception 'typeid suffix must be 26 characters';
  end if;

  if get_byte(dec, get_byte(v, 0)) = 255 or
     get_byte(dec, get_byte(v, 1)) = 255 or
     get_byte(dec, get_byte(v, 2)) = 255 or
     get_byte(dec, get_byte(v, 3)) = 255 or
     get_byte(dec, get_byte(v, 4)) = 255 or
     get_byte(dec, get_byte(v, 5)) = 255 or
     get_byte(dec, get_byte(v, 6)) = 255 or
     get_byte(dec, get_byte(v, 7)) = 255 or
     get_byte(dec, get_byte(v, 8)) = 255 or
     get_byte(dec, get_byte(v, 9)) = 255 or
     get_byte(dec, get_byte(v, 10)) = 255 or
     get_byte(dec, get_byte(v, 11)) = 255 or
     get_byte(dec, get_byte(v, 12)) = 255 or
     get_byte(dec, get_byte(v, 13)) = 255 or
     get_byte(dec, get_byte(v, 14)) = 255 or
     get_byte(dec, get_byte(v, 15)) = 255 or
     get_byte(dec, get_byte(v, 16)) = 255 or
     get_byte(dec, get_byte(v, 17)) = 255 or
     get_byte(dec, get_byte(v, 18)) = 255 or
     get_byte(dec, get_byte(v, 19)) = 255 or
     get_byte(dec, get_byte(v, 20)) = 255 or
     get_byte(dec, get_byte(v, 21)) = 255 or
     get_byte(dec, get_byte(v, 22)) = 255 or
     get_byte(dec, get_byte(v, 23)) = 255 or
     get_byte(dec, get_byte(v, 24)) = 255 or
     get_byte(dec, get_byte(v, 25)) = 255
  then
    raise exception 'typeid suffix must only use characters from the base32 alphabet';
  end if;

  if chr(get_byte(v, 0)) > '7' then
    raise exception 'typeid suffix must start with 0-7';
  end if;
  -- Transform base32 to binary array
  -- 6 bytes timestamp (48 bits)
  id = set_byte(id, 0, (get_byte(dec, get_byte(v, 0)) << 5) | get_byte(dec, get_byte(v, 1)));
  id = set_byte(id, 1, (get_byte(dec, get_byte(v, 2)) << 3) | (get_byte(dec, get_byte(v, 3)) >> 2));
  id = set_byte(id, 2, ((get_byte(dec, get_byte(v, 3)) & 3) << 6) | (get_byte(dec, get_byte(v, 4)) << 1) | (get_byte(dec, get_byte(v, 5)) >> 4));
  id = set_byte(id, 3, ((get_byte(dec, get_byte(v, 5)) & 15) << 4) | (get_byte(dec, get_byte(v, 6)) >> 1));
  id = set_byte(id, 4, ((get_byte(dec, get_byte(v, 6)) & 1) << 7) | (get_byte(dec, get_byte(v, 7)) << 2) | (get_byte(dec, get_byte(v, 8)) >> 3));
  id = set_byte(id, 5, ((get_byte(dec, get_byte(v, 8)) & 7) << 5) | get_byte(dec, get_byte(v, 9)));

  -- 10 bytes of entropy (80 bits)
  id = set_byte(id, 6, (get_byte(dec, get_byte(v, 10)) << 3) | (get_byte(dec, get_byte(v, 11)) >> 2));
  id = set_byte(id, 7, ((get_byte(dec, get_byte(v, 11)) & 3) << 6) | (get_byte(dec, get_byte(v, 12)) << 1) | (get_byte(dec, get_byte(v, 13)) >> 4));
  id = set_byte(id, 8, ((get_byte(dec, get_byte(v, 13)) & 15) << 4) | (get_byte(dec, get_byte(v, 14)) >> 1));
  id = set_byte(id, 9, ((get_byte(dec, get_byte(v, 14)) & 1) << 7) | (get_byte(dec, get_byte(v, 15)) << 2) | (get_byte(dec, get_byte(v, 16)) >> 3));
  id = set_byte(id, 10, ((get_byte(dec, get_byte(v, 16)) & 7) << 5) | get_byte(dec, get_byte(v, 17)));
  id = set_byte(id, 11, (get_byte(dec, get_byte(v, 18)) << 3) | (get_byte(dec, get_byte(v, 19)) >> 2));
  id = set_byte(id, 12, ((get_byte(dec, get_byte(v, 19)) & 3) << 6) | (get_byte(dec, get_byte(v, 20)) << 1) | (get_byte(dec, get_byte(v, 21)) >> 4));
  id = set_byte(id, 13, ((get_byte(dec, get_byte(v, 21)) & 15) << 4) | (get_byte(dec, get_byte(v, 22)) >> 1));
  id = set_byte(id, 14, ((get_byte(dec, get_byte(v, 22)) & 1) << 7) | (get_byte(dec, get_byte(v, 23)) << 2) | (get_byte(dec, get_byte(v, 24)) >> 3));
  id = set_byte(id, 15, ((get_byte(dec, get_byte(v, 24)) & 7) << 5) | get_byte(dec, get_byte(v, 25)));
  return encode(id, 'hex')::uuid;
end
$$
language plpgsql
immutable;
""")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS typeid_parse(text);")
    op.execute("DROP FUNCTION IF EXISTS base32_decode(text);")
