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


def test_generate_slug_returns_none_when_slugify_produces_empty():
    broker = BrokerFactory.build(name="___", slug="")

    assert generate_slug(broker) is None


def test_generate_slug_returns_existing_when_slug_non_blank():
    broker = BrokerFactory.build(name="Any Name", slug="kept-slug")

    assert generate_slug(broker) == "kept-slug"
