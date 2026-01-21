import pytest

import fastpg.fastpg as fastpg_mod


@pytest.fixture(autouse=True)
def reset_fastpg_registry():
    fastpg_mod._FASTPG_REGISTRY.clear()
    fastpg_mod._CURRENT_FASTPG_NAME.set("default")
    yield
    fastpg_mod._FASTPG_REGISTRY.clear()
    fastpg_mod._CURRENT_FASTPG_NAME.set("default")
