import re


def convert_values_to_hex_repr(yml_str_rep, key):
    return re.sub("{}: (\d+)".format(re.escape(key)),
                  lambda i: "{}: {:#x}".format(key,
                                               int(i.group(0)[i.group(0).find(": ") + 2:])),
                  yml_str_rep)