import yaml
from pathlib import Path

def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p.resolve()}")
    with p.open() as f:
        return yaml.safe_load(f)    