import yaml

from coilsnake.util.common.helper import lower_if_str
from coilsnake.util.common.yml import convert_values_to_hex_repr


def replace_field_in_yml(resource_name, resource_open_r, resource_open_w, key, new_key=None, value_map={}):
    """Replaces all instances of a key-value pair in a yml resource with a new key and/or value.
    :param resource_name: name of resource to operate on
    :param resource_open_r: resource open function (read-only)
    :param resource_open_w: resource open function (write-only)
    :param key: key of field(s) upon which which the replacement will be performed
    :param new_key: if provided, the function will replace all instances of the key with this value
    :param value_map: if provided, the function will replace any values of the provided key which are present as keys
                      in the map"""
    if new_key is None:
        new_key = key
    value_map = dict((lower_if_str(k), lower_if_str(v)) for k, v in value_map.iteritems())
    with resource_open_r(resource_name, "yml") as f:
        data = yaml.load(f, Loader=yaml.CSafeLoader)
        for i in data:
            if lower_if_str(data[i][key]) in value_map:
                data[i][new_key] = value_map[lower_if_str(data[i][key])]
                if new_key != key:
                    del data[i][key]
            elif new_key != key:
                data[i][new_key] = data[i][key]
                del data[i][key]
    with resource_open_w(resource_name, "yml") as f:
        yaml.dump(data, f, default_flow_style=False, Dumper=yaml.CSafeDumper)


def convert_values_to_hex_repr_in_yml_file(resource_name, resource_open_r, resource_open_w, keys):
    with resource_open_r(resource_name, "yml") as f:
        out = yaml.load(f, Loader=yaml.CSafeLoader)
        yml_str_rep = yaml.dump(out, default_flow_style=False, Dumper=yaml.CSafeDumper)

    for key in keys:
        yml_str_rep = convert_values_to_hex_repr(yml_str_rep, key)

    with resource_open_w(resource_name, "yml") as f:
        f.write(yml_str_rep)