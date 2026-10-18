import importlib
import re
from types import ModuleType


FEATURE_PATTERN = re.compile(r"^student[1-5]$")


class AdapterError(RuntimeError):
    """Raised when a requested feature adapter cannot be used."""


def normalize_feature(feature: str) -> str:
    normalized = (
        str(feature or "")
        .strip()
        .lower()
        .replace("-", "")
        .replace("_", "")
        .replace(" ", "")
    )

    if not FEATURE_PATTERN.fullmatch(normalized):
        raise AdapterError(
            "feature must identify student1, student2, student3, student4, or student5"
        )

    return normalized


def load_adapter(feature: str) -> ModuleType:
    normalized = normalize_feature(feature)
    module_name = f"adapters.{normalized}"

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            raise AdapterError(
                f"No Multi-Agent adapter is implemented for {normalized}"
            ) from exc
        raise

    gather_evidence = getattr(
        module,
        "gather_evidence",
        None,
    )

    if not callable(gather_evidence):
        raise AdapterError(
            f"{normalized} adapter does not provide gather_evidence()"
        )

    return module