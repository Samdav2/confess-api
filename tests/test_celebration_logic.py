from app.models.celebration import MusicType
from app.service.celebration_service import CelebrationService
import pytest
from unittest.mock import MagicMock

def test_calculate_price():
    service = CelebrationService(session=MagicMock())

    # Example 1: 3 images, No music -> 1000
    assert service.calculate_price(3, MusicType.NONE) == 1000.0

    # Example 2: 5 images, App music -> Base(1000) + Extra(2*500=1000) + Music(200) = 2200
    assert service.calculate_price(5, MusicType.APP_MUSIC) == 2200.0

    # Example 3: 6 images, Custom music -> Base(1000) + Extra(3*500=1500) + Music(500) = 3000
    assert service.calculate_price(6, MusicType.CUSTOM_MUSIC) == 3000.0

    # Boundary: 4 images, No music -> 1000 + 500 = 1500
    assert service.calculate_price(4, MusicType.NONE) == 1500.0

    # 2 images, App music -> 1000 + 200 = 1200
    assert service.calculate_price(2, MusicType.APP_MUSIC) == 1200.0

def test_validate_slug():
    service = CelebrationService(session=MagicMock())

    assert service.validate_slug("madeforinioluwa") is True
    assert service.validate_slug("happy-birthday") is True
    assert service.validate_slug("slug123") is True

    assert service.validate_slug("ab") is False # too short
    assert service.validate_slug("a" * 41) is False # too long
    assert service.validate_slug("MadeForInioluwa") is False # uppercase
    assert service.validate_slug("happy birthday") is False # spaces
    assert service.validate_slug("happy_birthday") is False # underscore not allowed (only hyphens)

if __name__ == "__main__":
    test_calculate_price()
    test_validate_slug()
    print("Tests passed!")
