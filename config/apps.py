from django.apps import AppConfig


class RuntimeConfig(AppConfig):
    name = "config"

    def ready(self) -> None:
        from config import checks  # noqa: F401
