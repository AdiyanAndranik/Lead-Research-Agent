from agent.email_generator import _count_words, _check_quality, _fallback_email


def test_word_count():
    assert _count_words("Hello world this is a test") == 6
    assert _count_words("") == 0
    assert _count_words("one") == 1


def test_quality_check_too_long():
    long_body = " ".join(["word"] * 200)
    flags = _check_quality(long_body, ["signal1", "signal2"])
    assert any("long" in f.lower() or "150" in f for f in flags)


def test_quality_check_too_short():
    short_body = "Hi there."
    flags = _check_quality(short_body, ["signal1", "signal2"])
    assert any("short" in f.lower() for f in flags)


def test_quality_check_banned_phrase():
    body = "I hope this finds you well. We have great synergy."
    flags = _check_quality(body, ["s1", "s2"])
    assert any("banned" in f.lower() for f in flags)


def test_quality_check_low_personalization():
    body = " ".join(["word"] * 90)
    flags = _check_quality(body, ["only one signal"])
    assert any("personalization" in f.lower() for f in flags)


def test_quality_check_clean_email():
    body = " ".join(["word"] * 100)
    flags = _check_quality(body, ["signal1", "signal2", "signal3"])
    assert flags == []


def test_fallback_email_structure():
    result = _fallback_email("TestCo", "Gor")
    assert len(result.drafts) == 1
    assert result.drafts[0].subject_line != ""
    assert result.drafts[0].body != ""
    assert "Fallback" in result.quality_flags[0]


def test_fallback_email_contains_company():
    result = _fallback_email("Acme Corp", "Gor")
    assert "Acme Corp" in result.drafts[0].body