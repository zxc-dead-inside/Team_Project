import re


def password_complexity_validator(password: str) -> str:
        if not re.search(r"[A-Z]", password):
            raise ValueError(
                "Password must contain at least one uppercase letter"
            )
        if not re.search(r"[a-z]", password):
            raise ValueError(
                "Password must contain at least one lowercase letter"
            )
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValueError(
                "Password must contain at least one special character"
            )
        return password