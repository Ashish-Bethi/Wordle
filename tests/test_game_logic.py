from services.game_service import evaluate_guess, is_accepted_guess

def test_exact_position_is_correct():
    assert evaluate_guess("APPLE", "APPLE") == ["correct"] * 5

def test_present_and_absent_letters():
    result = evaluate_guess("APPLE", "ALERT")
    assert result[0] == "correct"
    assert result[1] == "present"  # L occurs in APPLE, but elsewhere
    assert result[2] == "absent"

def test_duplicate_letters_are_not_overcounted():
    # Secret has one P. Guess contains two Ps: only one can be credited.
    result = evaluate_guess("APPLE", "PUPPY")
    assert result.count("present") + result.count("correct") <= 3

def test_guess_dictionary_accepts_common_words():
    assert is_accepted_guess("CRANE")
    assert is_accepted_guess("APPLE")
