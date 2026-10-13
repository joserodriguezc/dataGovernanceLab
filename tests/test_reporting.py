from dglab.reporting import fmt_money, fmt_num, fmt_pct


def test_fmt_money_uses_lab_currency_and_spanish_separators():
    assert fmt_money(1234567.8) == "US$ 1.234.568"
    assert fmt_money(-1077500) == "-US$ 1.077.500"
    assert fmt_money(45.5, decimals=2) == "US$ 45,50"


def test_fmt_num_and_pct():
    assert fmt_num(2582500) == "2.582.500"
    assert fmt_pct(0.425, decimals=1) == "42,5 %"


def test_fmt_pct_never_shows_negative_zero():
    assert fmt_pct(-0.0) == "0 %"
    assert fmt_pct(-0.001) == "0 %"
