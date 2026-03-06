def validate_header(header: str):

    if not header:
        raise ValueError("Header cannot be empty.")

    if not header.isupper():
        raise ValueError("Header must be uppercase.")

    if len(header.strip()) < 3:
        raise ValueError("Header too short.")

    return True


def validate_proposed_text(text: str):

    if not text:
        raise ValueError("Proposed text cannot be empty.")

    if len(text.strip()) < 10:
        raise ValueError("Proposed text too short.")

    return True
