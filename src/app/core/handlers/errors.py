class BaseError(Exception):

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DockerImageNotFoundError(BaseError):

    def __init__(self, message: str = "Docker image not found"):
        super().__init__(message, status_code=404)


class DockerInternalError(BaseError):

    def __init__(self, message: str = "Docker internal error"):
        super().__init__(message, status_code=500)


class NoLogsFoundError(BaseError):
    def __init__(self, message: str = "No logs found"):
        super().__init__(message, status_code=404)
