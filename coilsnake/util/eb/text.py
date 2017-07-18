class CharacterSubstitutions(object):
    character_substitutions = dict()


def standard_text_from_block(block, offset, max_length):
    str = ''
    for i in range(offset, offset + max_length):
        c = block[i]
        if c == 0:
            return str
        else:
            str += chr(c - 0x30)
    return str


def standard_text_to_byte_list(text, max_length):
    # First, substitute all of the characters
    if CharacterSubstitutions.character_substitutions:
        for k, v in CharacterSubstitutions.character_substitutions.items():
            text = text.replace(k, v)

    byte_list = []
    text_pos = 0
    while text_pos < len(text):
        c = text[text_pos]

        if c == '[':
            end_bracket_pos = text.find(']', text_pos)

            if end_bracket_pos == -1:
                raise ValueError("String contains '[' at position {} but no subsequent ']': {}".format(
                    text_pos, text
                ))

            bracket_bytes = text[text_pos+1:end_bracket_pos].split()
            for bracket_byte in bracket_bytes:
                if len(bracket_byte) != 2:
                    raise ValueError("String contains invalid hex number '{}', must be two digits: {}".format(
                        bracket_byte, text
                    ))

                try:
                    bracket_byte_value = int(bracket_byte, 16)
                except ValueError as e:
                    raise ValueError("String contains invalid hex number '{}': {}".format(
                        bracket_byte, text
                    ), e)

                byte_list.append(bracket_byte_value)

            text_pos = end_bracket_pos + 1
        else:
            byte_list.append(ord(c) + 0x30)
            text_pos += 1

    num_bytes = len(byte_list)
    if num_bytes > max_length:
        raise ValueError("String cannot be written in {} bytes or less: {}".format(
            max_length, text
        ))
    elif num_bytes < max_length:
        byte_list.append(0)

    return byte_list


def standard_text_to_block(block, offset, text, max_length):
    byte_list = standard_text_to_byte_list(text, max_length)
    block[offset:offset+len(byte_list)] = byte_list