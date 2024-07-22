# tests/test_simple.py

import pytest

class TestSimple:
    def test_assert_true(self):
        assert True

    @pytest.mark.parametrize("value", [True, 1, "non-empty string"])
    def test_parametrized_assert_true(self, value):
        assert value
