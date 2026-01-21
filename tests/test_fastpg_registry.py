import pytest

from fastpg.constants import ConnectionType
from fastpg.fastpg import (
    FastPG,
    create_fastpg,
    get_fastpg,
    register_fastpg,
    set_current_fastpg,
)
from fastpg.errors import FastPGInstanceNotConfiguredError


def _config():
    return {
        "read": {
            "TYPE": ConnectionType.READ,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
        "write": {
            "TYPE": ConnectionType.WRITE,
            "USER": "user",
            "PASSWORD": "pass",
            "DB": "db",
            "HOST": "localhost",
            "PORT": 5432,
        },
    }


def test_fastpg_timezone_defaults_to_utc_on_invalid_name():
    instance = FastPG(databases=_config(), fastpg_tz="Invalid/TZ")
    assert str(instance.TZ) == "UTC"


def test_registry_get_and_set_current():
    instance = create_fastpg(name="primary", databases=_config())
    assert get_fastpg() is instance
    set_current_fastpg("primary")
    assert get_fastpg() is instance


def test_get_fastpg_raises_when_missing():
    with pytest.raises(FastPGInstanceNotConfiguredError):
        get_fastpg("missing")


def test_set_current_fastpg_raises_when_missing():
    with pytest.raises(FastPGInstanceNotConfiguredError):
        set_current_fastpg("missing")


def test_register_fastpg_overrides_name():
    instance = FastPG(databases=_config())
    register_fastpg("primary", instance)
    assert get_fastpg("primary") is instance
