class ApiError(Exception):
    def __init__(self, status: int, error: str, message: str):
        self.status = status
        self.error = error
        self.message = message


def not_found():
    return ApiError(404, "not_found", "No encontramos el local o turno solicitado.")
