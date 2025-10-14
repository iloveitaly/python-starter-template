"""Add typeid_parse and base32_decode functions

Helpful when writing SQL queries directly vs using sqlalchemy.

Functions:
- typeid_parse(typeid_str text) -> uuid
  Parses a TypeID string (with optional prefix like "order_...") and returns a uuid.

- base32_decode(s text) -> uuid
  Decodes a 26-character TypeID suffix (Crockford base32) into a uuid.

Examples:
-- Parse a full TypeID (with or without prefix)
SELECT typeid_parse('scrn_01hxyzexampleexampleexample') AS id;

-- Join against a table storing uuids
SELECT *
FROM screening
WHERE screening.id = typeid_parse(:typeid);

-- Decode just the suffix
SELECT base32_decode('01hxyzexampleexampleexample') AS id;

-- Multiple-underscore prefixes are allowed
SELECT typeid_parse('doctor_note_schema_01hxyzexampleexampleexample');

-- Use in expressions
SELECT count(*)
FROM tickets
WHERE screening_id = typeid_parse(:screening_id);

Notes:
- Prefix (when present) must match ^[a-z]+(_[a-z]+)*$ and be <= 63 characters.
- Suffix must be 26 chars, use the base32 alphabet, and start with 0-7.

Revision ID: 489aff797e2e
Revises: cf868c4d11b7
Create Date: 2025-03-27 20:02:44.254927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import activemodel


# revision identifiers, used by Alembic.
revision: str = '489aff797e2e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    - https://github.com/jetify-com/typeid-sql/blob/main/sql/02_base32.sql
    - https://github.com/iloveitaly/opensource/blob/e9f63efec37b61d25f34d39b344646a1ff5bb7b2/typeid/typeid-sql/sql/03_typeid.sql#L70-L105
    """

    op.execute("""
-- squawk-ignore-file require-timeout-settings
create or replace function public.typeid_parse(typeid_str text)
 returns uuid
 language plpgsql
 immutable
as $function$
declare
  parts text[];  -- array to hold split parts of the string
  prefix text;
  suffix text;
begin
  if (typeid_str is null) then
    return null;
  end if;
  parts := string_to_array(typeid_str, '_');
  if array_length(parts, 1) = 1 then
    suffix := parts[1];
    prefix := '';
  else
    suffix := parts[array_length(parts, 1)];  -- last part is the suffix
    prefix := array_to_string(parts[1:array_length(parts, 1)-1], '_');  -- join all but last part with '_'
    if prefix = '' then
      raise exception 'typeid prefix cannot be empty with a delimiter';
    end if;
  end if;
  if prefix != '' then
    -- updated regex allows underscores in prefix, e.g., "doctor_note_schema"
    if not prefix ~ '^[a-z]+(_[a-z]+)*$' then
      raise exception 'typeid prefix must match the regular expression ^[a-z]+(_[a-z]+)*$';
    end if;
    if length(prefix) > 63 then
      raise exception 'typeid prefix must be at most 63 characters';
    end if;
  end if;
  return base32_decode(suffix)::uuid;
end
$function$
""")

    op.execute("""
create or replace function base32_decode(s text)
returns uuid as $$
declare
  dec bytea = '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF 00 01'::bytea ||
              '\\x02 03 04 05 06 07 08 09 FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF 0A 0B 0C'::bytea ||
              '\\x0D 0E 0F 10 11 FF 12 13 FF 14'::bytea ||
              '\\x15 FF 16 17 18 19 1A FF 1B 1C'::bytea ||
              '\\x1D 1E 1F FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF FF FF FF FF'::bytea ||
              '\\xFF FF FF FF FF FF'::bytea;
  v bytea = convert_to(s, 'UTF8');
  id bytea = '\\x00000000000000000000000000000000';
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

    # Encodes a UUID as a base32 string
    op.execute("""
create or replace function base32_encode(id uuid)
returns text
as $$
declare
  bytes bytea;
  alphabet bytea = '0123456789abcdefghjkmnpqrstvwxyz';
  output text = '';
begin
  bytes = uuid_send(id);

  -- 10 byte timestamp
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 0) & 224) >> 5));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 0) & 31)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 1) & 248) >> 3));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 1) & 7) << 2) | ((get_byte(bytes, 2) & 192) >> 6)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 2) & 62) >> 1));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 2) & 1) << 4) | ((get_byte(bytes, 3) & 240) >> 4)));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 3) & 15) << 1) | ((get_byte(bytes, 4) & 128) >> 7)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 4) & 124) >> 2));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 4) & 3) << 3) | ((get_byte(bytes, 5) & 224) >> 5)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 5) & 31)));

  -- 16 bytes of entropy
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 6) & 248) >> 3));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 6) & 7) << 2) | ((get_byte(bytes, 7) & 192) >> 6)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 7) & 62) >> 1));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 7) & 1) << 4) | ((get_byte(bytes, 8) & 240) >> 4)));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 8) & 15) << 1) | ((get_byte(bytes, 9) & 128) >> 7)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 9) & 124) >> 2));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 9) & 3) << 3) | ((get_byte(bytes, 10) & 224) >> 5)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 10) & 31)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 11) & 248) >> 3));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 11) & 7) << 2) | ((get_byte(bytes, 12) & 192) >> 6)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 12) & 62) >> 1));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 12) & 1) << 4) | ((get_byte(bytes, 13) & 240) >> 4)));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 13) & 15) << 1) | ((get_byte(bytes, 14) & 128) >> 7)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 14) & 124) >> 2));
  output = output || chr(get_byte(alphabet, ((get_byte(bytes, 14) & 3) << 3) | ((get_byte(bytes, 15) & 224) >> 5)));
  output = output || chr(get_byte(alphabet, (get_byte(bytes, 15) & 31)));

  return output;
end
$$
language plpgsql
immutable;
""")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS typeid_parse(text);")
    op.execute("DROP FUNCTION IF EXISTS base32_decode(text);")
    op.execute("DROP FUNCTION IF EXISTS base32_encode(text);")
