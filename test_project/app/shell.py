import sys
import importlib
import inspect
from pathlib import Path

from utils.color_print import print_green, print_red, print_yellow


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

schemas_path = BASE_DIR / 'app' / 'schemas'

# Load all classes from each module in app/schemas/
schema_classes = {}
for path in schemas_path.glob("*.py"):
    if path.name.startswith("_"):
        continue
    mod_name = path.stem
    full_mod = f"app.schemas.{mod_name}"
    module = importlib.import_module(full_mod)

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            schema_classes[name] = obj


from fastpg.core import (
    ASYNC_DB_READ,
    ASYNC_DB_WRITE,
)


banner = (
    "\n\n*** Welcome to FastAPI Shell! ***\n"
    f"Available: {', '.join(sorted(schema_classes))}"
)


async def async_on_shell_start():
    print_yellow(banner)
    print_yellow("[entry] Connecting to databases...")
    await ASYNC_DB_READ.connect()
    await ASYNC_DB_WRITE.connect()
    print_yellow("[entry] DB connections ready.")


async def async_cleanup():
    print_yellow("[cleanup] Closing DB connections...")
    await ASYNC_DB_READ.close()
    await ASYNC_DB_WRITE.close()
    print_yellow("[cleanup] DB connections closed.")


# Final context for shell
context = {
    'async_on_shell_start': async_on_shell_start,
    'async_cleanup': async_cleanup,  # Need to be manually called
    **schema_classes,
}

try:
    from IPython import start_ipython
    from traitlets.config.loader import Config

    c = Config()
    c.InteractiveShellApp.exec_lines = ['await async_on_shell_start()']

    start_ipython(argv=["--autoawait", "asyncio"], user_ns=context, config=c)
except ImportError:
    import code
    code.interact(local=context)
