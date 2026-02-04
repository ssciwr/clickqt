"""
Configures the test setup
"""

import re
import typing as t

import pytest

from click.testing import CliRunner


@pytest.fixture(scope="function")
def runner():
    """Uses the default runner"""
    return CliRunner()


def pytest_collection_modifyitems(items: t.Iterable[pytest.Function]):
    """
    Change the default test execution order
    Fundamental tests should be executed first
    """

    # The order of the test function names specifies the order the tests should be executed
    test_function_names = [
        "test_type_assignment",
        "test_widget_registry_command_names",
        "test_type_assignment_multiple_options",
        "test_type_assignment_multiple_commands",
    ]
    # First list should be at the front, the second one after the first one and so on
    move_to_front: list[list[pytest.Function]] = [
        [] for _ in range(len(test_function_names))
    ]

    items_removed = 0
    for i, item in enumerate(
        items[:]
    ):  # Iterate over a copy, because we are modifying the original list
        for j, name in enumerate(test_function_names):
            if (
                re.compile(f"^{name}(\\[|$)").search(item.name) is not None
            ):  # Due to parametrizied tests, the test names contain  (among other things) a "[" after the function name
                move_to_front[j].append(items.pop(i - items_removed))
                items_removed += 1
                break  # inner loop

    for test_functions_list in reversed(
        move_to_front
    ):  # First list should be at the front, so we need to insert the list (of lists) in reverse order
        for test_function in test_functions_list:
            items.insert(0, test_function)
