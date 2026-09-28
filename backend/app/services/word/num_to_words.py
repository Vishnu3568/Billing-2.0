from typing import Union


_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen"
]

_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
]


def _two_digit_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens = _TENS[n // 10]
    ones = _ONES[n % 10]
    return f"{tens} {ones}".strip() if ones else tens


def _three_digit_words(n: int) -> str:
    hundreds = n // 100
    remainder = n % 100
    parts = []
    if hundreds > 0:
        parts.append(f"{_ONES[hundreds]} Hundred")
    if remainder > 0:
        parts.append(_two_digit_words(remainder))
    return " ".join(parts).strip()


def amount_to_words_inr(amount: Union[int, float, str, None]) -> str:
    """
    Converts a numeric amount into Indian Currency words.
    Example: 4020 -> 'Four Thousand Twenty Rupees Only'
    Example: 4020.50 -> 'Four Thousand Twenty Rupees and Fifty Paise Only'
    """
    if amount is None:
        return ""

    try:
        if isinstance(amount, str):
            clean_str = amount.replace("₹", "").replace(",", "").strip()
            num = float(clean_str)
        else:
            num = float(amount)
    except (ValueError, TypeError):
        return str(amount)

    if num < 0:
        return f"Negative {amount_to_words_inr(-num)}"

    int_part = int(num)
    paise_part = int(round((num - int_part) * 100))

    if int_part == 0 and paise_part == 0:
        return "Zero Rupees Only"

    # Indian numbering: Crores (10,000,000), Lakhs (100,000), Thousands (1,000), Hundreds (100)
    crores = int_part // 10000000
    remainder = int_part % 10000000

    lakhs = remainder // 100000
    remainder = remainder % 100000

    thousands = remainder // 1000
    remainder = remainder % 1000

    hundreds_part = remainder

    parts = []
    if crores > 0:
        parts.append(f"{_three_digit_words(crores)} Crore")
    if lakhs > 0:
        parts.append(f"{_two_digit_words(lakhs)} Lakh")
    if thousands > 0:
        parts.append(f"{_two_digit_words(thousands)} Thousand")
    if hundreds_part > 0:
        parts.append(_three_digit_words(hundreds_part))

    rupees_str = " ".join(parts).strip()
    result = f"{rupees_str} Rupees" if rupees_str else ""

    if paise_part > 0:
        paise_words = _two_digit_words(paise_part)
        if result:
            result = f"{result} and {paise_words} Paise Only"
        else:
            result = f"{paise_words} Paise Only"
    else:
        result = f"{result} Only"

    return result.strip()
