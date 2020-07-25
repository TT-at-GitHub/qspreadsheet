

def ordinal_str(n):
    '''
    Returns the ordinal number of a given integer, as a string.
    eg. 1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    '''
    if 10 <= n % 100 < 20:
        return '{0}th'.format(n)
    else:
        ord = {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, 'th')
        return '{0}{1}'.format(n, ord)    