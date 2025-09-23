from pathlib import Path

def load_seeds(path: str = "seeds.txt") -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Seed file not found: {file_path.resolve()}")
    with file_path.open() as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]