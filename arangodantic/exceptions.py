class ArangodanticError(Exception):
    """Generic Arangodantic error class."""

    pass


class ModelNotFoundError(ArangodanticError):
    pass


class ConfigError(ArangodanticError):
    pass