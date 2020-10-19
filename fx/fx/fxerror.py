"""
Custom error types

"""

class ArgumentValidationError(ValueError):
    """
    Raised when the type of an argument to a function is incorrect

    Args:

        arg {str}: argument name

        fn_name {str}: function name

        correct_type {type}: the argument's correct type

    """

    def __init__(self, arg, fn_name, correct_type):
        self.error = "Argument '{0}' passed to {1}() is not a {2}".format(
            arg, fn_name, correct_type)

    def __str__(self):
        return self.error


class InvalidReturnTypeError(ValueError):
    """
    When function's return value is the wrong type.
    """

    def __init__(self, return_type, fn_name, correct_type):
        self.error = "Invalid return type {0} for '{1}()', expected {2}".format(
            return_type, fn_name, correct_type)

    def __str__(self):
        return self.error
