def escapeString(str):
    return '"' + str.replace('"', '\\"') + '"'

def unescapeString(str):
    str = str.strip()
    if str.startswith('"'):
        return (str[1:-1]).replace('\\"', '"')
    else:
        return str

