import sys, os
import numpy as np
import pandas as pd


def ordinal_str(n):
    '''Returns the ordinal number of a given integer, as a string.
        eg 1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    '''
    if 10 <= n % 100 < 20:
        return '{0}th'.format(n)
    else:
        ord = {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, 'th')
        return '{0}{1}'.format(n, ord)


def free_filename(fullname: str) -> str:
    name, ext = os.path.splitext(fullname)
    i = 0
    while os.path.isfile(fullname):
        fullname = f'{name}({str(i)}){ext}'
        i += 1
    return fullname


def normalize_filename(filename: str, replace_with=''):
    invalid = '/\\:*?"><"|'
    if replace_with and replace_with in invalid:
        replace_with = '_'

    for char in filename:
        if char in invalid:
            filename = filename.replace(char, replace_with)
    return filename


def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return np.floor(n*multiplier + 0.5) / multiplier


def is_iterable(obj):
    return (hasattr(obj, '__getitem__')
        or hasattr(obj, '__iter__'))


def is_sequence(obj):
    return (not isinstance(obj, str)
        and is_iterable(obj))


def as_sequence(obj, convert_dtype=list):
    if is_sequence(obj):
        return obj

    obj = convert_dtype((obj))
    if not is_sequence(obj):
        raise TypeError('The type of `convert_dtype` is not a sequence')
    return obj


def _validate_column(column):
    if column is None:
        raise ValueError('`column` cannot be None if object is DataFrame')
    if not isinstance(column, str):
        raise TypeError('`column` must be `str`')


def mask(obj: pd.DataFrame or pd.Series, values, column=None) -> pd.Series:
    if obj is None:
        raise ValueError('`obj` is None')
    if values is None:
        raise ValueError('`values` is None')

    values = as_sequence(values)

    if isinstance(obj, pd.Series):
        return obj.isin(values)
    elif isinstance(obj, pd.DataFrame):
        _validate_column(column)
        return obj[column].isin(values)
    else:
        raise TypeError('`obj` is not instance of Series or DataFrame')


def invmask(obj: pd.DataFrame or pd.Series, values, column=None) -> pd.Series:
    return ~mask(obj, values, column)


def ntrues(obj: pd.DataFrame or pd.Series, values, column=None) -> int:
    return mask(obj, values, column).sum()


def nnot_trues(obj: pd.DataFrame or pd.Series, values, column=None) -> int:
    return (~mask(obj, values, column)).sum()


def mask_loc(obj: pd.DataFrame or pd.Series, values, column=None):
    return obj.loc[mask(obj, values, column)]


def mask_invloc(obj: pd.DataFrame or pd.Series, values, column=None):
    return obj.loc[~mask(obj, values, column)]


def split_loc(obj: pd.DataFrame or pd.Series, values, column=None) -> tuple:
    obj_mask = mask(obj, values, column)
    return obj.loc[obj_mask], obj.loc[~obj_mask]


def nulls_mask(obj:pd.DataFrame or pd.Series, column=None) -> pd.Series:
    if obj is None:
        raise ValueError('`obj` is None')

    if isinstance(obj, pd.Series):
        return obj.isnull()
    elif isinstance(obj, pd.DataFrame):
        _validate_column(column)
        return obj[column].isnull()
    else:
        raise TypeError('`obj` is not instance of Series or DataFrame')


def not_nulls_mask(obj:pd.DataFrame or pd.Series, column=None) -> pd.Series:
    return ~nulls_mask(obj, column)


def nulls_loc(obj: pd.DataFrame or pd.Series, values, column=None) -> tuple:
    return obj.loc[nulls_mask(obj, column)]


def not_nulls_loc(obj: pd.DataFrame or pd.Series, values, column=None) -> tuple:
    return obj.loc[~nulls_mask(obj, column)]


def nulls_split(obj: pd.DataFrame or pd.Series, column=None) -> tuple:
    obj_mask = nulls_mask(obj, column)
    return obj.loc[~obj_mask], obj.loc[obj_mask]


def nnulls(obj: pd.DataFrame or pd.Series, column=None) -> int:
    return nulls_mask(obj, column).sum()


def nnot_nulls(obj: pd.DataFrame or pd.Series, column=None) -> int:
    return (~nulls_mask(obj, column)).sum()


def _parse_input(**kwargs):
    column = kwargs.pop('column')
    keepna = kwargs.pop('keepna')

    for name, obj in kwargs.items():
        if obj is None:
            continue
        if not isinstance(obj, (pd.Series, pd.DataFrame)):
            raise TypeError(f'Invalid type for `{name}`. Expected Series or DataFrame')
        if isinstance(obj, pd.DataFrame):
            _validate_column(column)
            obj = obj[column]
        if not keepna:
            obj = obj.dropna()
        kwargs[name] = obj
    return kwargs


def intersection(first, second, column=None, keepna=False) -> np.ndarray:
    if first is None and second is None:
        return None

    kwargs = _parse_input(first=first, second=second,
        column=column, keepna=keepna)

    first = kwargs['first']
    second = kwargs['second']

    if first is None:
        return second
    elif second is None:
        return first
    else:
        return first[first.isin(second)].unique()


def setdiff(first, second, column=None, keepna=False, assume_unique=False) -> np.ndarray:
    kwargs = _parse_input(first=first, second=second,
        column=column, keepna=keepna)

    first = kwargs['first']
    second = kwargs['second']

    if first is None:
        return second
    elif second is None:
        return first
    else:
        if not assume_unique:
            first = first.unique()
            second = second.unique()
        return np.setdiff1d(first, second, assume_unique=True)


def to_mixed_intstr(s: pd.Series) -> pd.Series:
    res = s.copy()
    tmp = pd.to_numeric(s, errors='coerce')
    res.loc[tmp.notnull()] = tmp.loc[tmp.notnull()].apply(int).apply(str)
    return res


def to_coerced_intstr(s: pd.Series) -> pd.Series:
    res = pd.to_numeric(s, errors='coerce')
    res.loc[res.notnull()] = res.loc[res.notnull()].apply(int).apply(str)
    return res


def to_intstr(s: pd.Series) -> pd.Series:
    return s.apply(float).apply(int).apply(str)


def sort_mix_values(s: pd.Series, str_position='first', na_position='last'):
    """
    Sort by the values, where 'str' and 'numeric' values are sorted separately.

    Sort a Series in ascending or descending order.

    Parameters
    ----------
    s : pd.Series
    str_position : {'first' or 'last'}, default 'first'
    na_position : {'first' or 'last'}, default 'last'
    """    
    if s is None:
        raise ValueError('`s` is None')

    # split null values, if any
    num_nulls = nnulls(s)
    if num_nulls:
        s, nulls = nulls_split(s)

    numeric = pd.to_numeric(s, errors='coerce')

    # split str values if any
    num_strings = nnulls(numeric)
    if num_strings:
        numeric, str_ndx = nulls_split(numeric)
        strings = s[str_ndx.index]

    result = numeric.sort_values(ascending=True)

    if num_strings:
        strings = strings.sort_values()
        if str_position == 'first':
            result = strings.append(result)
        elif str_position == 'last':
            result = result.append(strings)

    if num_nulls:
        if na_position == 'first':
            result = nulls.append(result)
        elif na_position == 'last':
            result = result.append(nulls)
            
    return result
