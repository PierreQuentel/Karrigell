def get_strings(script):
    src = open(script,'rb').readline
    strings = []
    import tokenize,token
    state = None
    for info in tokenize.tokenize(src):
        typ,token_string = token.tok_name[info[0]],info[1]
        if state is None and typ == "NAME" and token_string == "_":
            state = True
        elif state is True and typ == "OP" and token_string == "(":
            state = "ready"
        elif state == "ready":
            if typ == "STRING":
                _string = eval(token_string)
                if not _string in strings:
                    strings.append(_string)
            state = None
    return strings

def guess_encoding(filename):
    # from meta tag in file
    encoding = None
    data = open(filename,encoding='ascii',errors='ignore').read()
    import re
    mo = re.search(r'(?i)<meta\s+(.*?)charset=(.*)>',data)
    if mo:
        encoding = mo.groups()[1].strip('"')
    return encoding

def get_strings_kt(script):
    encoding = guess_encoding(script) or ENCODING
    src = open(script,encoding=encoding)
    import shlex
    parser = shlex.shlex(instream=src)
    strings = []
    state = None
    while True:
        token = parser.get_token()
        if token == parser.eof:
            break
        if state is None and token == "_":
            state = True
        elif state is True and token == "[":
            state = "ready"
        elif state == "ready":
            if not token in strings:
                strings.append(token)
            state = None
    return strings
