from backend.app.services.lead_parser import run_parser


def test_plain_company_name():
    result = run_parser(text="Linear")
    assert result.accepted == 1
    assert result.parsed[0].company_name == "Linear"
    assert result.parsed[0].domain is None


def test_plain_url():
    result = run_parser(text="https://linear.app")
    assert result.accepted == 1
    assert result.parsed[0].domain == "linear.app"
    assert result.parsed[0].company_name == "Linear"


def test_name_and_domain():
    result = run_parser(text="Linear, linear.app")
    assert result.accepted == 1
    assert result.parsed[0].company_name == "Linear"
    assert result.parsed[0].domain == "linear.app"


def test_linkedin_url():
    result = run_parser(text="https://linkedin.com/company/linear")
    assert result.accepted == 1
    assert result.parsed[0].linkedin_url == "https://www.linkedin.com/company/linear"


def test_multiple_lines():
    text = """Linear, linear.app
Stripe, stripe.com
Notion
https://retool.com"""
    result = run_parser(text=text)
    assert result.accepted == 4
    assert result.total_submitted == 4


def test_deduplication():
    text = """Linear, linear.app
Linear, linear.app
Stripe"""
    result = run_parser(text=text)
    assert result.accepted == 2
    assert result.duplicates_removed == 1


def test_csv_input():
    csv_content = b"company,url\nLinear,linear.app\nStripe,stripe.com\n"
    result = run_parser(csv_content=csv_content)
    assert result.accepted == 2
    assert result.parsed[0].company_name == "Linear"
    assert result.parsed[1].domain == "stripe.com"