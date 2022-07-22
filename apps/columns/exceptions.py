class FunctionNotFound(Exception):
    def __init__(self, function) -> None:
        message = f"Function '{function}' does not exist"
        self.function = function
        super().__init__(message)


class ColumnNotFound(Exception):
    def __init__(self, column, columns) -> None:
        message = f"Column '{column}' does not exist"
        self.column = column
        self.columns = columns
        super().__init__(message)


class ArgumentError(Exception):
    def __init__(self, function, args):
        super().__init__()
        self.function = function
        self.args = args


class ColumnAttributeError(Exception):
    def __init__(self, column=None, value=None, function=None):
        super().__init__()
        self.column = column
        self.function = function
        self.value = value


class ParseError(Exception):
    def __init__(self, formula, columns):
        super().__init__()
        self.formula = formula
        self.columns = columns
