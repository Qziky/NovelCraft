class NovelCraftError(Exception):
    pass


class ConfigError(NovelCraftError):
    pass


class APIError(NovelCraftError):
    pass


class APIConnectionError(APIError):
    pass


class APIRateLimitError(APIError):
    pass


class FileError(NovelCraftError):
    pass


class OutlineFormatError(FileError):
    pass
