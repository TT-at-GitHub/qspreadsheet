"""
Decorators

https://learning-python.com/rangetest.html
https://www.pythoncentral.io/validate-python-function-parameters-and-return-types-with-decorators/

"""
import sys, os
from functools import wraps 
import warnings
from fx import fx
from fx.fxerror import ArgumentValidationError, InvalidReturnTypeError

trace = __debug__


def accepts(**kwargtypes):
    '''
    Decorator to check the parameter types of a given function.

    Args:
        kwargtypes: keyword args of types or type tuples
        eg. @accepts(a=int, b=str, c=float, d=(list, tuple))

    Sample usage:

        @accepts(a=int, b=int)
        def func(a, b):         
            return a + b

        @accepts(a=(int, float), b=(int, float))
        def funcf(a, b):
            return a + b

        func(2, 3)          # fine:  int and int
        funcf(2, 3.0)       # fine:  int or float
        funcf("2", 3)       # error: str and int 
            ArgumentValidationError: Argument 'a' passed to func() is not a (<class 'int'>, <class 'float'>)

    '''

    def accepts_wrapper(fn):
        # will work in python 2.6+ and python 3+
        code = fn.__code__ if sys.version_info[0] == 3 else fn.func_code
        allargs = code.co_varnames[:code.co_argcount]
        fn_name = fn.__name__

        @wraps(fn)  # to avoid loosing fn's docstring
        def fn_wrapper(*pargs, **kargs):
            positionals = list(allargs)[:len(pargs)]

            for (argname, typ) in kwargtypes.items():
                if argname in kargs:
                    if not isinstance(kargs[argname], typ):
                        raise ArgumentValidationError(
                            argname, fn_name, typ)
                elif argname in positionals:
                    position = positionals.index(argname)
                    if not isinstance(pargs[position], typ):
                        raise ArgumentValidationError(
                            argname, fn_name, typ)
                else:
                    # assume not passed: default
                    if trace:
                        print("Argument '{0}' defaulted".format(argname))

            return fn(*pargs, **kargs)  # execute
        return fn_wrapper
    return accepts_wrapper


def debug_accepts(**kwargtypes):
    '''
    Decorator to check the parameter types of a given function.

    NOTE: To improve performance, checks are executed only if __debug__ == 'True'

    Args:
        kwargtypes: keyword args of types or type tuples
        eg. @accepts(a=int, b=str, c=float, d=(list, tuple))

    Sample usage:

        @debug_accepts(a=int, b=int)
        def func(a, b):         
            return a + b

        @debug_accepts(a=(int, float), b=(int, float))
        def funcf(a, b):
            return a + b

        func(2, 3)          # fine:  int and int
        funcf(2, 3.0)       # fine:  int or float
        funcf("2", 3)       # error: str and int 
            ArgumentValidationError: Argument 'a' passed to func() is not a (<class 'int'>, <class 'float'>)

    '''

    def accepts_wrapper(fn):
        if not __debug__:                   # True if "python -O main.py args.."
            return fn                       # wrap if debugging else use original
        else:
            # will work in python 2.6+ and python 3+
            code = fn.__code__ if sys.version_info[0] == 3 else fn.func_code
            allargs = code.co_varnames[:code.co_argcount]
            fn_name = fn.__name__

            @wraps(fn)  # to avoid loosing fn's docstring
            def fn_wrapper(*pargs, **kargs):
                positionals = list(allargs)[:len(pargs)]

                for (argname, typ) in kwargtypes.items():
                    if argname in kargs:
                        if not isinstance(kargs[argname], typ):
                            raise ArgumentValidationError(
                                argname, fn_name, typ)
                    elif argname in positionals:
                        position = positionals.index(argname)
                        if not isinstance(pargs[position], typ):
                            raise ArgumentValidationError(
                                argname, fn_name, typ)
                    else:
                        # assume not passed: default
                        if trace:
                            print("Argument '{0}' defaulted".format(argname))

                return fn(*pargs, **kargs)  # execute
            return fn_wrapper
    return accepts_wrapper


def returns(*return_type):
    '''
    Validates the return type of a given function.

    Sample usage:

        @returns((int, float))
        def func(a, b):
            return a + b

        func(2, 3)          # fine:  returns int
        func(2, 3.0)        # fine:  returns float
        func("2", 3)        # error: InvalidReturnTypeError - Invalid return type <class 'str'> for func()

    '''
    def returns_wrapper(fn):
        # No return type has been specified.
        if len(return_type) == 0:
            raise TypeError('You must specify a return type.')

        @wraps(fn)
        def fn_wrapper(*fn_args, **fn_kwargs):
            # More than one return type has been specified.
            if len(return_type) > 1:
                raise TypeError('You must specify one return type.')

            # Since the decorator receives a tuple of arguments
            # and the is only ever one object returned, we'll just
            # grab the first parameter.
            expected_return_type = return_type[0]

            # We'll execute the function, and
            # take a look at the return type.
            return_value = fn(*fn_args, **fn_kwargs)

            if not isinstance(return_value, expected_return_type):
                raise InvalidReturnTypeError(
                    type(return_value), fn.__name__, expected_return_type)

            return return_value

        return fn_wrapper
    return returns_wrapper


def debug_returns(*return_type):
    '''
    Validates the return type of a given function.

    NOTE: To improve performance, checks are executed only if __debug__ == 'True'

    Sample usage:

        @debug_returns((int, float))
        def func(a, b):
            return a + b

        func(2, 3)          # fine:  returns int
        func(2, 3.0)        # fine:  returns float
        func("2", 3)        # error: InvalidReturnTypeError - Invalid return type <class 'str'> for func()

    '''
    def returns_wrapper(fn):
        if not __debug__:                   # True if "python -O main.py args.."
            return fn                       # wrap if debugging else use original
        else:
            # No return type has been specified.
            if len(return_type) == 0:
                raise TypeError('You must specify a return type.')

            @wraps(fn)
            def fn_wrapper(*fn_args, **fn_kwargs):
                # More than one return type has been specified.
                if len(return_type) > 1:
                    raise TypeError('You must specify one return type.')

                # Since the decorator receives a tuple of arguments
                # and the is only ever one object returned, we'll just
                # grab the first parameter.
                expected_return_type = return_type[0]

                # We'll execute the function, and
                # take a look at the return type.
                return_value = fn(*fn_args, **fn_kwargs)

                if not isinstance(return_value, expected_return_type):
                    raise InvalidReturnTypeError(
                        type(return_value), fn.__name__, expected_return_type)

                return return_value

            return fn_wrapper
    return returns_wrapper


def rangetest(**kw_range_checks):
    """
    Decorator to perform value range checks on the parameters of a given function.

    Args:
        kw_range_checks: keyword args of types or type tuples
        eg. @accepts(a=int, b=str, c=float, d=(list, tuple))

    Sample usage:

        @rangetest(age=(0, 120))
        def person(name, age):
            print('%s is %s years old' % (name, age))

        person('Bob Smith', 45)             # fine
        person(age=45, name='Bob Smith')    # fine
        person('Bob Smith', age=200)        # error
            TypeError: person() argument 'age' not in 0..120

        @rangetest(M=(1, 12), D=(1, 31), Y=(0, 2009))
        def birthday(M, D, Y):
            print('birthday = {0}/{1}/{2}'.format(M, D, Y))

        birthday(5, Y=1963, D=31)           # fine
        birthday(5, 32, 1963)               # error
            TypeError: birthday() argument 'D' not in 1..31

    """

    # fn_wrapper remembers fn and kw_range_checks
    def rangetest_wrapper(fn):
        # will work in python 2.6+ and python 3+
        code = fn.__code__ if sys.version_info[0] == 3 else fn.func_code
        allargs = code.co_varnames[:code.co_argcount]
        fn_name = fn.__name__

        @wraps(fn)  # to avoid loosing fn's docstring
        def fn_wrapper(*args, **kwargs):
                # all args match first N args by position
                # the rest must be in kwargs or omitted defaults
            positionals = list(allargs)[:len(args)]

            for (argname, (low, high)) in kw_range_checks.items():
                    # for all args to be checked
                if argname in kwargs:
                    # was passed by name
                    if kwargs[argname] < low or kwargs[argname] > high:
                        errmsg = "{0}() argument '{1}' not in {2}..{3}".format(
                            fn_name, argname, low, high)
                        raise TypeError(errmsg)

                elif argname in positionals:
                    # was passed by position
                    position = positionals.index(argname)
                    if args[position] < low or args[position] > high:
                        errmsg = "{0} argument() '{1}' not in {2}..{3}".format(
                            fn_name, argname, low, high)
                        raise TypeError(errmsg)
                else:
                    # assume not passed: default
                    if trace:
                        print("Argument '{0}' defaulted".format(argname))

            return fn(*args, **kwargs)    # okay: run original call
        return fn_wrapper
    return rangetest_wrapper


def debug_rangetest(**kw_range_checks):
    """
    Decorator to perform value range checks on the parameters of a given function.

    NOTE: To improve performance, checks are executed only if __debug__ == 'True'

    Args:
        kw_range_checks: keyword args of types or type tuples
        eg. @accepts(a=int, b=str, c=float, d=(list, tuple))

    Sample usage:

        @debug_rangetest(age=(0, 120))
        def person(name, age):
            print('%s is %s years old' % (name, age))

        person('Bob Smith', 45)             # fine
        person(age=45, name='Bob Smith')    # fine
        person('Bob Smith', age=200)        # error
            TypeError: person() argument 'age' not in 0..120

        @debug_rangetest(M=(1, 12), D=(1, 31), Y=(0, 2009))
        def birthday(M, D, Y):
            print('birthday = {0}/{1}/{2}'.format(M, D, Y))

        birthday(5, Y=1963, D=31)           # fine
        birthday(5, 32, 1963)               # error
            TypeError: birthday() argument 'D' not in 1..31

    """

    # fn_wrapper remembers fn and kw_range_checks
    def rangetest_wrapper(fn):
        if not __debug__:                   # True if "python -O main.py args.."
            return fn                       # wrap if debugging else use original
        else:
            # will work in python 2.6+ and python 3+
            code = fn.__code__ if sys.version_info[0] == 3 else fn.func_code
            allargs = code.co_varnames[:code.co_argcount]
            fn_name = fn.__name__

            @wraps(fn)  # to avoid loosing fn's docstring
            def fn_wrapper(*args, **kwargs):
                    # all args match first N args by position
                    # the rest must be in kwargs or omitted defaults
                positionals = list(allargs)[:len(args)]

                for (argname, (low, high)) in kw_range_checks.items():
                        # for all args to be checked
                    if argname in kwargs:
                        # was passed by name
                        if kwargs[argname] < low or kwargs[argname] > high:
                            errmsg = "{0}() argument '{1}' not in {2}..{3}".format(
                                fn_name, argname, low, high)
                            raise TypeError(errmsg)

                    elif argname in positionals:
                        # was passed by position
                        position = positionals.index(argname)
                        if args[position] < low or args[position] > high:
                            errmsg = "{0} argument() '{1}' not in {2}..{3}".format(
                                fn_name, argname, low, high)
                            raise TypeError(errmsg)
                    else:
                        # assume not passed: default
                        if trace:
                            print("Argument '{0}' defaulted".format(argname))

                return fn(*args, **kwargs)    # okay: run original call
            return fn_wrapper
    return rangetest_wrapper


def doublewrap(func):

    @wraps(func)
    def new_decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # called as @decorator
            return func(args[0])
        else:
            # called as @decorator(*args, **kwargs)
            return lambda actual: func(actual, *args, *kwargs)
    return new_decorator


@doublewrap
def deprecated(func, msg=None):
    
    warnings_msg = f'Call to deprecated function `{func.__name__}`'
    if msg is not None:
        warnings_msg = '\n'.join([warnings_msg, msg])

    @wraps(func)
    def wrapper(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn(warnings_msg, category=DeprecationWarning, stacklevel=5)
        warnings.simplefilter('default', DeprecationWarning)
        return func(*args, **kwargs)
    
    return wrapper


def decorate_methods(decorator):
    
    @wraps(decorator)
    def wrapper(cls):
        for name, val in vars(cls).items():
            if callable(val):
                setattr(cls, name, decorator(val))
        return cls 
    return wrapper