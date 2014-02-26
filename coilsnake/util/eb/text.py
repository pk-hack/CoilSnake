def standard_text_from_block(block, offset, max_length):
    str = ''
    for i in range(offset, offset + max_length):
        c = block[i]
        if c == 0:
            return str
        else:
            str += chr(c - 0x30)
    return str


def standard_text_to_block(block, offset, text, max_length):
    pos = 0
    for i in text:
        if pos >= max_length:
            break
        block[offset + pos] = ord(i) + 0x30
        pos += 1
    if pos < max_length:
        block[offset + pos] = 0