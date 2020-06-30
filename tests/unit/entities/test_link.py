from unittest.mock import MagicMock, call

import pytest

from link.entities import link


@pytest.fixture
def local_repo():
    name = "local_repo"
    local_repo = MagicMock(name=name)
    local_repo.__contains__ = MagicMock(name=name + ".__contains__", return_value=True)
    local_repo.__repr__ = MagicMock(name=name + ".__repr__", return_value=name)
    return local_repo


@pytest.fixture
def outbound_repo():
    name = "outbound_repo"
    outbound_repo = MagicMock(name=name)
    outbound_repo.__contains__ = MagicMock(name=name + ".__contains__", return_value=True)
    outbound_repo.__repr__ = MagicMock(name=name + ".__repr__", return_value=name)
    return outbound_repo


@pytest.fixture
def link_instance(local_repo, outbound_repo):
    return link.Link(local_repo, outbound_repo)


class TestInit:
    def test_if_local_repository_is_stored_as_instance_attribute(self, link_instance, local_repo):
        assert link_instance.local_repo is local_repo

    def test_if_outbound_repository_is_stored_as_instance_attribute(self, link_instance, outbound_repo):
        assert link_instance.outbound_repo is outbound_repo

    def test_if_link_attribute_is_set_in_local_repository(self, link_instance, local_repo):
        assert local_repo.link is link_instance

    def test_if_link_attribute_is_set_in_outbound_repository(self, link_instance, outbound_repo):
        assert outbound_repo.link is link_instance


class TestPresentInLocalRepository:
    def test_if_presence_is_checked_in_local_repository(self, identifiers, link_instance, local_repo):
        for identifier in identifiers:
            link_instance.present_in_local_repo(identifier)
        assert local_repo.__contains__.mock_calls == [call(identifier) for identifier in identifiers]

    def test_if_correct_value_is_returned(self, identifiers, link_instance, local_repo):
        assert all(link_instance.present_in_local_repo(identifier) is True for identifier in identifiers)


class TestPresentInOutboundRepository:
    def test_if_presence_is_checked_in_outbound_repository(self, identifiers, link_instance, outbound_repo):
        for identifier in identifiers:
            link_instance.present_in_outbound_repo(identifier)
        assert outbound_repo.__contains__.mock_calls == [call(identifier) for identifier in identifiers]

    def test_if_correct_value_is_returned(self, identifiers, link_instance, outbound_repo):
        assert all(link_instance.present_in_outbound_repo(identifier) is True for identifier in identifiers)


def test_if_delete_in_outbound_repository_deletes_in_outbound_repository(identifiers, link_instance, outbound_repo):
    link_instance.delete_in_outbound_repo(identifiers)
    outbound_repo.delete.assert_called_once_with(identifiers)


def test_repr(link_instance):
    assert repr(link_instance) == "Link(local_repo, outbound_repo)"
