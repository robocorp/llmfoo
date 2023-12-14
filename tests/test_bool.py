from llmfoo import is_statement_true


def test_is_statement_true_with_default_criteria():
    assert is_statement_true("Earth is a planet.")
    assert not is_statement_true("1 + 2 = 5")


def test_is_statement_true_with_own_criteria():
    assert not is_statement_true("Temperature outside is -2 degrees celsius",
                                 criteria="Temperature above 0 degrees celsius")
    assert is_statement_true("1984 was written by George Orwell",
                             criteria="George Orwell is the author of 1984")


def test_is_statement_true_criteria_can_change_truth_value():
    assert is_statement_true("Earth is 3rd planet from the Sun")
    assert not is_statement_true("Earth is 3rd planet from the Sun",
                                 criteria="Earth is stated to be 5th planet from the Sun")
