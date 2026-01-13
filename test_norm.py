import re

def normalize_mana_cost(cost):
    if not cost:
        return ""
    # Extract all symbols in braces, sort them, and join them back
    symbols = re.findall(r"\{[^}]+\}", cost)
    if not symbols:
        return cost
    symbols.sort()
    return "".join(symbols)

test_cases = [
    ("{1}{W}{U}", "{1}{U}{W}"),
    ("{W}{U}{1}", "{1}{U}{W}"),
    ("{R}{R}{G}", "{G}{R}{R}"),
    ("{10}{W}", "{10}{W}"),
    ("{W}{10}", "{10}{W}"),
    ("{W}{U}{B}{R}{G}", "{B}{G}{R}{U}{W}"),
    ("", ""),
    ("1WU", "1WU"), # No braces case
]

for cost, expected in test_cases:
    result = normalize_mana_cost(cost)
    print(f"Input: {cost:15} | Result: {result:15} | Pass: {result == expected}")
