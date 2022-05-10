class FunctionNotFound(Exception):
    def __init__(self, function) -> None:
        message = f"'{function}' does not exist"
        self.function = function
        super().__init__(message)


class ColumnNotFound(Exception):
    def __init__(self, column) -> None:
        message = f"'{column}' does not exist"
        self.column = column
        super().__init__(message)
