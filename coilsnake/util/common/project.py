import yaml


def replace_field(resource_name, old_key, new_key, value_map, resource_open_r, resource_open_w):
    if new_key is None:
        new_key = old_key
        value_map = dict((k.lower() if (isinstance(k, str)) else k, v) for k, v in value_map.iteritems())
        with resource_open_r(resource_name, 'yml') as f:
            data = yaml.load(f, Loader=yaml.CSafeLoader)
            for i in data:
                if data[i][old_key] in value_map:
                    if isinstance(data[i][old_key], str):
                        data[i][new_key] = value_map[data[i][old_key].lower()].lower()
                    else:
                        data[i][new_key] = value_map[data[i][old_key]].lower()
                else:
                    data[i][new_key] = data[i][old_key]
                if new_key != old_key:
                    del data[i][old_key]
        with resource_open_w(resource_name, 'yml') as f:
            yaml.dump(data, f, default_flow_style=False, Dumper=yaml.CSafeDumper)