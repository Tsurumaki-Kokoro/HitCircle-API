# app/themes/theme_manager.py
import importlib.util
from pathlib import Path
from .theme_interface import ThemeStrategy


def load_theme_strategy(theme_path: Path) -> ThemeStrategy:
    spec = importlib.util.spec_from_file_location("theme_strategy", theme_path)
    theme_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(theme_module)
    strategy_instance = theme_module.get_theme_strategy()
    return strategy_instance


def discover_and_load_themes(feature_name: str) -> dict[str, ThemeStrategy]:
    base_theme_path = Path(__file__).parent / feature_name
    themes = {}

    for theme in base_theme_path.iterdir():
        if theme.is_dir() and (theme / "theme.py").exists():
            theme_strategy = load_theme_strategy(theme / "theme.py")
            themes[theme.name] = theme_strategy

    return themes
