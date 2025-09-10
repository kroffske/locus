def join_path(parts):
    out = ""
    for part in parts:
        seg = part.strip("/")
        if out:
            out += "/" + seg
        else:
            out = seg
    return out

