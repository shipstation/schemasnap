import ruamel.yaml


RUAMEL_STYLE_ARGS = {
    'indent': 4,
    'block_seq_indent': 2,
}


def represent_none(self, data):
    # Write null's as "null" instead of nothing.
    return self.represent_scalar(u'tag:yaml.org,2002:null', u'null')


ruamel.yaml.representer.RoundTripRepresenter.add_representer(type(None), represent_none)


def dump(parsed_yaml):
    return ruamel.yaml.dump(parsed_yaml, Dumper=ruamel.yaml.RoundTripDumper, **RUAMEL_STYLE_ARGS)


def load(yaml_str):
    return ruamel.yaml.load(yaml_str, ruamel.yaml.RoundTripLoader)


def load_empty():
    """When no existing doc exists to be loaded, use this."""
    # NB: Unfortunately it's not as easy as `load('{}')` because it writes back
    #    out `{key: 1, ...` to match that format. Is there an ordereddict we can
    #    initialize from?
    v = load('key: value')
    del v['key']
    return v
