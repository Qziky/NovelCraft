import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from novel_cli.core.config import Settings, mask_key


def test_settings_defaults():
    s = Settings()
    assert s.api_key == ""
    assert s.model == "gpt-4"


def test_mask_key():
    assert mask_key("sk-1234567890abcdef") == "sk-1***********cdef"
    assert mask_key("short") == "****"
    assert mask_key("") == "****"


def test_settings_from_dict():
    s = Settings(api_key="test-key", model="mimo-v2.5")
    assert s.api_key == "test-key"
    assert s.model == "mimo-v2.5"
