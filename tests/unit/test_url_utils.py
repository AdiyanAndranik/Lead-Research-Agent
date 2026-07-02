from backend.app.core.url_utils import (
    extract_domain,
    extract_linkedin_url,
    extract_company_name_from_domain,
    normalize_domain,
    is_blacklisted,
    looks_like_url,
    build_homepage_url,
)


def test_extract_domain_full_url():
    assert extract_domain("https://linear.app/changelog") == "linear.app"


def test_extract_domain_www():
    assert extract_domain("https://www.stripe.com") == "stripe.com"


def test_extract_domain_bare():
    assert extract_domain("linear.app") == "linear.app"


def test_extract_domain_plain_name():
    assert extract_domain("Linear") is None


def test_extract_domain_with_path():
    assert extract_domain("https://retool.com/product/workflows") == "retool.com"


def test_extract_linkedin():
    assert extract_linkedin_url(
        "https://www.linkedin.com/company/linear/"
    ) == "https://www.linkedin.com/company/linear"


def test_extract_linkedin_no_scheme():
    assert extract_linkedin_url(
        "linkedin.com/company/stripe"
    ) == "https://www.linkedin.com/company/stripe"


def test_extract_linkedin_not_present():
    assert extract_linkedin_url("https://linear.app") is None


def test_company_name_from_domain():
    assert extract_company_name_from_domain("linear.app") == "Linear"
    assert extract_company_name_from_domain("my-company.io") == "My Company"
    assert extract_company_name_from_domain("stripe.com") == "Stripe"


def test_normalize_domain():
    assert normalize_domain("Linear.App") == "linear.app"
    assert normalize_domain("stripe.com/") == "stripe.com"


def test_blacklisted():
    assert is_blacklisted("gmail.com") is True
    assert is_blacklisted("linear.app") is False


def test_looks_like_url():
    assert looks_like_url("https://linear.app") is True
    assert looks_like_url("linear.app") is True
    assert looks_like_url("Linear") is False


def test_build_homepage_url():
    assert build_homepage_url("linear.app") == "https://linear.app"
    assert build_homepage_url("Stripe.COM/") == "https://stripe.com"

    