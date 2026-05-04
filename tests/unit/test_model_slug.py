from slugify import slugify

from app.factories.broker import BrokerFactory
from app.lib.model_slug import generate_slug


def test_broker_save_generates_slug_from_name():
    name = "Acme Insurance LLC"

    broker = BrokerFactory.save(name=name)

    assert broker.slug == slugify(name)


def test_generate_slug_appends_suffix_when_slug_taken():
    name = "Slug Collision Test Co"
    expected_base = slugify(name)

    first = BrokerFactory.save(name=name)
    second = BrokerFactory.save(name=name)

    assert first.slug == expected_base
    assert second.slug == f"{expected_base}-2"


def test_generate_slug_returns_none_when_name_blank():
    broker = BrokerFactory.build(name="   ", slug="")

    assert generate_slug(broker) is None


def test_generate_slug_returns_none_when_name_is_none():
    class Row:
        id = 1
        name: str | None = None
        slug = ""

        @classmethod
        def where(cls, *conditions):
            class Q:
                def no_autoflush(self):
                    return self

                def exists(self):
                    raise AssertionError("query should not run when name is None")

            return Q()

        def is_new(self):
            return True

    assert generate_slug(Row()) is None


def test_generate_slug_returns_none_when_slugify_produces_empty():
    broker = BrokerFactory.build(name="___", slug="")

    assert generate_slug(broker) is None


def test_generate_slug_searches_by_slug_only_for_new_row():
    class Q:
        def no_autoflush(self):
            return self

        def exists(self):
            return False

    class Row:
        id = 1
        name = "Acme"
        slug = ""
        conditions: list[object] = []

        @classmethod
        def where(cls, *conditions: object):
            cls.conditions = list(conditions)
            return Q()

        def is_new(self):
            return True

    assert generate_slug(Row()) == "acme"
    assert len(Row.conditions) == 1


def test_generate_slug_excludes_saved_row_from_slug_search():
    class Q:
        def no_autoflush(self):
            return self

        def exists(self):
            return False

    class Row:
        id = 1
        name = "Acme"
        slug = ""
        conditions: list[object] = []

        @classmethod
        def where(cls, *conditions: object):
            cls.conditions = list(conditions)
            return Q()

        def is_new(self):
            return False

    assert generate_slug(Row()) == "acme"
    assert len(Row.conditions) == 2
