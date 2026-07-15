import re


def mask_name(name: str | None) -> str:
    """Mask a person's name (e.g., 'Arjun Rao' -> 'A**** R**')."""
    if not name:
        return "Unknown"
    parts = name.strip().split()
    masked_parts = []
    for p in parts:
        if len(p) <= 2:
            masked_parts.append(p[0] + "*")
        else:
            masked_parts.append(p[0] + "*" * (len(p) - 1))
    return " ".join(masked_parts)


def mask_phone(phone: str | None) -> str:
    """Mask a phone number (e.g., '9876543212' -> 'XXXXXX3212')."""
    if not phone:
        return "XXXXXX"
    phone_str = str(phone).strip()
    if len(phone_str) <= 4:
        return "X" * len(phone_str)
    return "X" * (len(phone_str) - 4) + phone_str[-4:]


def mask_account(account: str | None) -> str:
    """Mask a bank account number (e.g., '123456789012' -> 'XXXXXXXX9012')."""
    if not account:
        return "XXXXXXXX"
    acc_str = str(account).strip()
    if len(acc_str) <= 4:
        return "X" * len(acc_str)
    return "X" * (len(acc_str) - 4) + acc_str[-4:]


def mask_address(address: str | None) -> str:
    """Mask a local street address, preserving the district or city (e.g., '21, Malleshwaram, Bengaluru' -> 'XXXX, Malleshwaram, Bengaluru')."""
    if not address:
        return "XXXX, Karnataka"
    parts = address.split(",")
    if len(parts) <= 1:
        return "XXXX, Karnataka"
    
    # Mask street-level details (first few parts), keep last part (city/district)
    masked_parts = ["XXXX" for _ in range(len(parts) - 1)]
    masked_parts.append(parts[-1].strip())
    return ", ".join(masked_parts)


def mask_brief_facts(facts: str | None) -> str:
    """Mask potential phone numbers and account numbers inside narrative texts/brief facts."""
    if not facts:
        return ""
    # Mask 10-12 digit numbers (phone/accounts)
    masked = re.sub(r"\b\d{10,12}\b", "XXXXXXXX1234", facts)
    # Mask 16 digit card/account numbers
    masked = re.sub(r"\b\d{16}\b", "XXXXXXXXXXXXXXXX", masked)
    return masked
