import string
import random

async def generate_referral_code(username: str, length: int = 6) -> str:
    """
    Generate a referral code from username.

    Format: [First 3 chars of username]CS[random alphanumeric]
    Example: "john_doe" -> "JOHCS8X2K9"
    Returns:
        A unique referral code string
    """
    prefix = username[:3].upper()
    middle = "CS"
    random_suffix = ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=length)
    )
    referral_code = f"{prefix}{middle}{random_suffix}"
    return referral_code
