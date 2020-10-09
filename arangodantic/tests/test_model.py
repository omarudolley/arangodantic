import pytest

from arangodantic import CONF, ModelNotFoundError
from arangodantic.tests.conftest import ExtendedIdentity, Identity, Link, SubModel


@pytest.mark.asyncio
async def test_save_and_load_model(identity_collection):
    identity = Identity(name="John Doe")
    await identity.save()

    assert identity.key_ is not None
    assert identity.rev_ is not None

    loaded_identity = await Identity.load(identity.key_)
    assert identity.key_ == loaded_identity.key_


@pytest.mark.asyncio
async def test_delete_model(identity_collection):
    identity = Identity(name="Jane Doe")
    await identity.save()
    assert await identity.delete() is True

    with pytest.raises(ModelNotFoundError):
        await identity.delete()

    assert await identity.delete(ignore_missing=True) is False


@pytest.mark.asyncio
async def test_reload(identity_collection):
    identity = Identity(name="Jane Doe")
    with pytest.raises(ModelNotFoundError):
        await identity.reload()

    await identity.save()

    loaded_identity = await Identity.load(identity.key_)
    assert identity.key_ == loaded_identity.key_

    identity.name = "Jane Austen"
    await identity.save()

    assert loaded_identity.name == "Jane Doe"
    await loaded_identity.reload()
    assert loaded_identity.name == "Jane Austen"


@pytest.mark.asyncio
async def test_locking(identity_collection):
    identity = Identity(name="James Doe")
    await identity.save()

    second_lock = CONF.lock(Identity.get_lock_name(identity.key_))

    # Lock and reload the identity
    async with identity.lock_and_reload():
        # Verify the lock is held
        assert await second_lock.acquire(block=False) is False

    # Verify the lock is not held any longer
    try:
        assert await second_lock.acquire(block=False) is True
    finally:
        await second_lock.release()

    # Lock and load as new identity
    async with Identity.lock_and_load(identity.key_) as _:
        # Verify the lock is held
        assert await second_lock.acquire(block=False) is False

    # Verify the lock is not held any longer
    try:
        assert await second_lock.acquire(block=False) is True
    finally:
        await second_lock.release()


@pytest.mark.asyncio
async def test__before_save(extended_identity_collection):
    identity = ExtendedIdentity(name="John Doe")
    await identity.save(extra="foo")
    identity = await ExtendedIdentity.load(identity.key_)
    assert identity.extra == "foo"


@pytest.mark.asyncio
async def test_sub_models(extended_identity_collection):
    sub = SubModel(text="foo")
    identity = ExtendedIdentity(name="John Doe", sub=sub)
    await identity.save()

    identity = await ExtendedIdentity.load(identity.key_)
    assert isinstance(identity.sub, SubModel)
    assert identity.sub.text == "foo"

    identity.sub = None
    await identity.reload()
    assert isinstance(identity.sub, SubModel)
    assert identity.sub.text == "foo"


@pytest.mark.asyncio
async def test_edge_model(identity_collection, link_collection):
    alice = Identity(name="Alice")
    await alice.save()
    bob = Identity(name="Bob")
    await bob.save()

    link = Link(_from=alice, _to=bob, type="Knows")
    await link.save()

    await link.reload()
    assert link.from_ == alice.id_
    assert link.to_ == bob.id_