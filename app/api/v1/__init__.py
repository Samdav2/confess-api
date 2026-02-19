import pkgutil, importlib
from fastapi import APIRouter

router = APIRouter()

for _, module_name, _ in pkgutil.iter_modules(__path__):
    if module_name == "auth":
        continue
    module = importlib.import_module(f"{__name__}.{module_name}")
    if hasattr(module, "router"):
        # Use hyphens instead of underscores for URLs
        if module_name == "confess":
            url_prefix = "/anonymous"
            tag_name = "Anonymous Link"
        else:
            url_prefix = f"/{module_name.replace('_', '-')}"
            tag_name = module_name.replace('_', ' ').title()

        router.include_router(module.router, prefix=url_prefix, tags=[tag_name])
