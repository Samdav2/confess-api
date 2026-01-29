import pkgutil, importlib
from fastapi import APIRouter

router = APIRouter()

for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name == "auth":
        continue
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "router"):
        # Use hyphens instead of underscores for URLs
        url_prefix = f"/{module_name.replace('_', '-')}"
        router.include_router(module.router, prefix=url_prefix, tags=[module_name.replace('_', ' ').title()])
