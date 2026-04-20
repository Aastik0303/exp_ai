"""
Utility functions for Indian Rupee formatting and accurate math.
Handles proper INR comma placement and Decimal-based arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP


def format_inr(amount) -> str:
    """
    Format number in Indian Rupee style with proper comma placement.
    Example: 1234567.89 → ₹12,34,567.89
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    negative = amount < 0
    amount = abs(amount)

    amount_decimal = Decimal(str(amount)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    integer_part, decimal_part = str(amount_decimal).split(".")

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        rest_with_commas = ""
        while len(rest) > 2:
            rest_with_commas = "," + rest[-2:] + rest_with_commas
            rest = rest[:-2]
        rest_with_commas = rest + rest_with_commas
        formatted_int = rest_with_commas + "," + last_three

    result = f"₹{formatted_int}.{decimal_part}"
    return f"-{result}" if negative else result


def format_inr_short(amount) -> str:
    """
    Short INR format for compact display.
    Example: 1,50,000 → ₹1.50L, 1,00,00,000 → ₹1.00Cr
    """
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return "₹0"

    negative = amount < 0
    amount = abs(amount)

    if amount >= 10000000:
        result = f"₹{amount / 10000000:.2f}Cr"
    elif amount >= 100000:
        result = f"₹{amount / 100000:.2f}L"
    elif amount >= 1000:
        result = f"₹{amount / 1000:.2f}K"
    else:
        result = f"₹{amount:.2f}"

    return f"-{result}" if negative else result


def safe_add(*values) -> float:
    """Accurate addition using Decimal to avoid floating point errors."""
    total = Decimal("0")
    for v in values:
        try:
            total += Decimal(str(v))
        except Exception:
            continue
    return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def safe_subtract(a, b) -> float:
    """Accurate subtraction using Decimal."""
    try:
        result = Decimal(str(a)) - Decimal(str(b))
        return float(result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except Exception:
        return 0.0


def safe_percentage(part, whole) -> float:
    """Safe percentage calculation - avoids division by zero."""
    try:
        if float(whole) == 0:
            return 0.0
        return round((float(part) / float(whole)) * 100, 2)
    except Exception:
        return 0.0


def safe_round(value, decimals=2) -> float:
    """Accurately round numbers using Decimal."""
    try:
        return float(
            Decimal(str(value)).quantize(
                Decimal("0." + "0" * decimals), rounding=ROUND_HALF_UP
            )
        )
    except Exception:
        return 0.0