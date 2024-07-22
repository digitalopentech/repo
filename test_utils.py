# tests/test_utils.py

import pytest
from src.utils import get_env_prefix, get_schema_name, uppercase_for_dict_keys

class TestUtils:
    def test_get_env_prefix(self):
        assert get_env_prefix() == "env"

    @pytest.mark.parametrize("domain, table, expected", [
        ("mydomain", "my-table", "mydomain_my_table"),
        ("testdomain", "test-table", "testdomain_test_table"),
        ("domain", "table", "domain_table")
    ])
    def test_get_schema_name(self, domain, table, expected):
        assert get_schema_name(domain, table) == expected

    @pytest.mark.parametrize("input_dict, expected_dict", [
        ({"key": "value"}, {"KEY": "value"}),
        ({"key": {"nested_key": "nested_value"}}, {"KEY": {"NESTED_KEY": "nested_value"}}),
        ({}, {}),
        ({"key": None}, {"KEY": None})
    ])
    def test_uppercase_for_dict_keys(self, input_dict, expected_dict):
        assert uppercase_for_dict_keys(input_dict) == expected_dict
