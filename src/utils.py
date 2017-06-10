def replace_nth_ocurrence(source, n, letter, new_value):
    ind = source.index(letter, n)
    source[ind] = new_value
    return source

def fill_dict(array):
    to_return = dict()
    none_list = ['actor', 'number', 'first_name', 'last_name']
    for i in array:
        to_return[i] = None if i in none_list else 0
    return to_return
