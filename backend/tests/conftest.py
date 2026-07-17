from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_rooms_path() -> Path:
    return FIXTURES / "sample_rooms.json"
