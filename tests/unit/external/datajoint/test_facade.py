from unittest.mock import MagicMock
from dataclasses import is_dataclass

import pytest
from datajoint import Part

from link.base import Base
from link.external.datajoint.facade import TableEntityDTO, TableFacade
from link.adapters.datajoint.abstract_facade import AbstractTableEntityDTO


@pytest.fixture
def flag_table_names():
    return ["MyFlag", "MyOtherFlag"]


@pytest.fixture
def is_present_in_flag_table(flag_table_names):
    return {flag_table_name: is_present for flag_table_name, is_present in zip(flag_table_names, [False, True])}


@pytest.fixture
def flag_table_spies(flag_table_names, is_present_in_flag_table):
    flag_table_spies = dict()
    for name in flag_table_names:
        spy = MagicMock(name=name + "Spy", spec=Part)
        spy.__and__.return_value.__contains__.return_value = is_present_in_flag_table[name]
        flag_table_spies[name] = spy
    return flag_table_spies


@pytest.fixture
def primary_key():
    return dict(primary_attr1=0, primary_attr2=1)


@pytest.fixture
def master_entity(primary_key):
    return dict(primary_key, non_primary_attr1=0, non_primary_attr2=1)


@pytest.fixture
def table_spy(flag_table_spies, master_entity):
    table_spy = MagicMock(name="table_spy", flag_table_names=flag_table_names)
    table_spy.proj.return_value.fetch.return_value = "primary_keys"
    table_spy.proj.return_value.__and__.return_value.fetch.return_value = "primary_keys_in_restriction"
    table_spy.__and__.return_value.fetch1.return_value = master_entity
    for name, flag_table_spy in flag_table_spies.items():
        setattr(table_spy, name, flag_table_spy)
    return table_spy


@pytest.fixture
def part_entities():
    return {name: name + "_entities" for name in ["MyPart", "MyOtherPart"]}


@pytest.fixture
def part_table_spies(part_entities):
    part_table_spies = dict()
    for name, entities in part_entities.items():
        spy = MagicMock(name=name + "Spy", spec=Part)
        spy.__and__.return_value.fetch.return_value = entities
        part_table_spies[name] = spy
    return part_table_spies


@pytest.fixture
def table_factory_spy(table_spy, part_table_spies, flag_table_spies):
    return MagicMock(
        name="table_factory_spy", return_value=table_spy, part_tables=part_table_spies, flag_tables=flag_table_spies
    )


@pytest.fixture
def download_path():
    return "download_path"


@pytest.fixture
def table_facade(table_factory_spy, download_path):
    return TableFacade(table_factory_spy, download_path)


class TestTableEntityDTO:
    def test_if_subclass_of_abstract_table_entity_dto(self):
        assert issubclass(TableEntityDTO, AbstractTableEntityDTO)

    def test_if_dataclass(self):
        assert is_dataclass(TableEntityDTO)

    def test_if_primary_key_is_stored_as_instance_attribute(self, primary_key, master_entity):
        assert TableEntityDTO(primary_key, master_entity).primary_key is primary_key

    def test_if_master_entity_is_stored_as_instance_attribute(self, primary_key, master_entity):
        assert TableEntityDTO(primary_key, master_entity).master_entity is master_entity

    def test_if_part_entities_are_stored_as_instance_attribute(self, primary_key, master_entity, part_entities):
        assert TableEntityDTO(primary_key, master_entity, part_entities=part_entities).part_entities is part_entities

    def test_if_part_entities_are_empty_dict_if_not_provided(self, primary_key, master_entity):
        assert TableEntityDTO(primary_key, master_entity).part_entities == dict()


def test_if_table_facade_is_subclass_of_base():
    assert issubclass(TableFacade, Base)


def test_if_table_factory_is_stored_as_instance_attribute(table_facade, table_factory_spy):
    assert table_facade.table_factory is table_factory_spy


def test_if_download_path_is_stored_as_instance_attribute(table_facade, download_path):
    assert table_facade.download_path == download_path


class TestPrimaryKeysProperty:
    @pytest.fixture(autouse=True)
    def primary_keys(self, table_facade):
        return table_facade.primary_keys

    def test_if_table_is_projected_to_primary_keys(self, table_spy):
        table_spy.proj.assert_called_once_with()

    def test_if_primary_keys_are_fetched_from_projected_table(self, table_spy):
        table_spy.proj.return_value.fetch.assert_called_once_with(as_dict=True)

    def test_if_primary_keys_are_returned(self, primary_keys):
        assert primary_keys == "primary_keys"


@pytest.fixture
def primary_keys_in_restriction(table_facade):
    return table_facade.get_primary_keys_in_restriction("restriction")


@pytest.mark.usefixtures("primary_keys_in_restriction")
class TestGetPrimaryKeysInRestriction:
    def test_if_call_to_table_factory_is_correct(self, table_factory_spy):
        table_factory_spy.assert_called_once_with()

    def test_if_table_is_projected_to_primary_keys(self, table_spy):
        table_spy.proj.assert_called_once_with()

    def test_if_projected_table_is_restricted(self, table_spy):
        table_spy.proj.return_value.__and__.assert_called_once_with("restriction")

    def test_if_primary_keys_are_fetched_from_restricted_table(self, table_spy):
        table_spy.proj.return_value.__and__.return_value.fetch.assert_called_once_with(as_dict=True)

    def test_if_primary_keys_are_returned(self, primary_keys_in_restriction):
        assert primary_keys_in_restriction == "primary_keys_in_restriction"


@pytest.fixture
def flags(table_facade, primary_key):
    return table_facade.get_flags(primary_key)


@pytest.mark.usefixtures("flags")
class TestGetFlags:
    def test_if_flag_tables_are_restricted(self, flag_table_spies, primary_key):
        for flag_table in flag_table_spies.values():
            flag_table.__and__.assert_called_once_with(primary_key)

    def test_if_presence_of_primary_key_in_restricted_flag_tables_is_checked(self, flag_table_spies, primary_key):
        for flag_table in flag_table_spies.values():
            flag_table.__and__.return_value.__contains__.assert_called_once_with(primary_key)

    def test_if_returned_flags_are_correct(self, is_present_in_flag_table, flags):
        assert flags == is_present_in_flag_table


@pytest.fixture
def fetched_entity(table_facade, primary_key):
    return table_facade.fetch(primary_key)


@pytest.mark.usefixtures("fetched_entity")
class TestFetch:
    def test_if_call_to_table_factory_is_correct(self, table_factory_spy):
        table_factory_spy.assert_called_once_with()

    def test_if_table_is_restricted(self, table_spy, primary_key):
        table_spy.__and__.assert_called_once_with(primary_key)

    def test_if_master_entity_is_fetched(self, table_spy, download_path):
        table_spy.__and__.return_value.fetch1.assert_called_once_with(download_path=download_path)

    def test_if_part_tables_are_restricted(self, part_table_spies, primary_key):
        for part in part_table_spies.values():
            part.__and__.assert_called_once_with(primary_key)

    def test_if_part_entities_are_fetched_from_part_tables(self, part_table_spies, download_path):
        for part in part_table_spies.values():
            part.__and__.return_value.fetch.assert_called_once_with(as_dict=True, download_path=download_path)

    def test_if_table_entity_dto_is_returned(self, fetched_entity, primary_key, master_entity, part_entities):
        assert fetched_entity == TableEntityDTO(
            primary_key=primary_key, master_entity=master_entity, part_entities=part_entities
        )


class TestInsert:
    @pytest.fixture
    def insert(self, table_facade, table_entity_dto):
        table_facade.insert(table_entity_dto)

    @pytest.fixture
    def table_entity_dto(self, primary_key, master_entity, part_entities):
        return TableEntityDTO(primary_key=primary_key, master_entity=master_entity, part_entities=part_entities)

    @pytest.mark.usefixtures("insert")
    def test_if_call_to_table_factory_is_correct(self, table_factory_spy):
        table_factory_spy.assert_called_once_with()

    @pytest.mark.usefixtures("insert")
    def test_if_master_entity_is_inserted(self, table_spy, master_entity):
        table_spy.insert1.assert_called_once_with(master_entity)

    @pytest.mark.usefixtures("insert")
    def test_if_part_entities_are_inserted(self, part_table_spies, part_entities):
        for name, part in part_table_spies.items():
            part.insert.assert_called_once_with(part_entities[name])

    def test_if_master_entity_is_inserted_before_part_entities(
        self, table_facade, table_entity_dto, table_spy, part_table_spies
    ):
        table_spy.insert1.side_effect = RuntimeError
        try:
            table_facade.insert(table_entity_dto)
        except RuntimeError:
            pass
        for part in part_table_spies.values():
            part.insert.assert_not_called()


class TestDelete:
    @pytest.fixture
    def delete(self, table_facade, primary_key):
        table_facade.delete(primary_key)

    @pytest.mark.usefixtures("delete")
    def test_if_part_tables_are_restricted(self, part_table_spies, primary_key):
        for part in part_table_spies.values():
            part.__and__.assert_called_once_with(primary_key)

    @pytest.mark.usefixtures("delete")
    def test_if_part_entities_are_deleted(self, part_table_spies):
        for part in part_table_spies.values():
            part.__and__.return_value.delete_quick.assert_called_once_with()

    @pytest.mark.usefixtures("delete")
    def test_if_call_to_table_factory_is_correct(self, table_factory_spy):
        table_factory_spy.assert_called_once_with()

    @pytest.mark.usefixtures("delete")
    def test_if_table_is_restricted(self, table_spy, primary_key):
        table_spy.__and__.assert_called_once_with(primary_key)

    @pytest.mark.usefixtures("delete")
    def test_if_master_table_entity_is_deleted(self, table_spy):
        table_spy.__and__.return_value.delete_quick.assert_called_once_with()

    def test_if_part_entities_are_deleted_before_master_entity(
        self, table_facade, primary_key, table_spy, part_table_spies
    ):
        table_spy.__and__.return_value.delete_quick.side_effect = RuntimeError
        try:
            table_facade.delete(primary_key)
        except RuntimeError:
            pass
        for part in part_table_spies.values():
            part.__and__.return_value.delete_quick.assert_called_once_with()


@pytest.fixture
def flag_table_name(flag_table_names):
    return flag_table_names[0]


@pytest.fixture
def flag_table_spy(flag_table_spies, flag_table_name):
    return flag_table_spies[flag_table_name]


def test_if_flag_is_enabled(table_facade, primary_key, flag_table_name, flag_table_spy):
    table_facade.enable_flag(primary_key, flag_table_name)
    flag_table_spy.insert1.assert_called_once_with(primary_key)


@pytest.fixture
def disable_flag(table_facade, primary_key, flag_table_name):
    table_facade.disable_flag(primary_key, flag_table_name)


@pytest.mark.usefixtures("disable_flag")
class TestDisableFlag:
    def test_if_flag_table_is_restricted(self, flag_table_spy, primary_key):
        flag_table_spy.__and__.assert_called_once_with(primary_key)

    def test_if_flag_is_deleted(self, flag_table_spy):
        flag_table_spy.__and__.return_value.delete_quick.assert_called_once_with()


@pytest.fixture
def execute(request, table_facade):
    getattr(table_facade, request.cls.method_name)()


@pytest.mark.usefixtures("execute")
class TestTransaction:
    method_name = None

    @pytest.fixture(params=["start_transaction", "commit_transaction", "cancel_transaction"], autouse=True)
    def method_name(self, request):
        request.cls.method_name = request.param
        return request.param

    def test_if_call_to_table_factory_is_correct(self, table_factory_spy):
        table_factory_spy.assert_called_once_with()

    def test_if_transaction_related_method_is_executed_in_connection(self, table_spy, method_name):
        getattr(table_spy.connection, method_name).assert_called_once_with()
