def flatten(list_of_lists):
    out = []
    for sub in list_of_lists:
        for item in sub:
            out.append(item)
    return out
