#!/usr/bin/env python

import os
import argparse
import json
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class JsonSchema2Popo(object):
    """Converts a JSON Schema to a Plain Old Python Object class"""
    definitions = {}

    TEMPLATES_FOLDER = 'templates/'
    CLASS_TEMPLATE_FNAME = '_class.tmpl'
    
    # add default value for type
    J2P_TYPES = {
        'string': 'str',
        'integer': 'int',
        'number': 'float',
        'object': 'type',
        'array': 'list',
        'boolean': 'bool',
        'null': 'None'
    }
    
    def __init__(self):
        self.jinja = Environment(loader=FileSystemLoader(os.path.join(os.path.sep, SCRIPT_DIR, self.TEMPLATES_FOLDER)), trim_blocks=True)

    def load(self, json_schema_file):
        self.process(json.load(json_schema_file))

    def process(self, json_schema):
        # process base obj, properties and replace $refs
        for _obj_name, _obj in json_schema['definitions'].items():
            model = {}
            model['name'] = _obj_name
            if 'type' in _obj:
                model['type'] = _obj['type']
            if 'required' in _obj:
                model['required'] = _obj['required']

            model['properties'] = []
            if 'properties' in _obj:
                for _prop_name, _prop in _obj['properties'].items():
                    # support $ref, allOf..., array len > 1
                    if 'type' in _prop and isinstance(_prop['type'], list) and len(_prop['type']) == 0:
                        _type = self.J2P_TYPES[_prop['type'][0]]
                    elif 'type' in _prop and isinstance(_prop['type'], str):
                        _type = self.J2P_TYPES[_prop['type']]
                    else:
                        _type = None
                    
                    _default = None
                    if 'default' in _prop:
                        _default = _prop['default']
                        if _type == 'str':
                            _default = "'{}'".format(_default)
                    else:
                        if _type == 'str':
                            _default = "''"
                        elif _type == 'int' or _type == 'float':
                            _default = 0
                        elif _type == 'list':
                            _default = []
                        elif _type == 'bool':
                            _default = False

                    _enum = None
                    if 'enum' in _prop:
                        _enum = _prop['enum']

                    prop = {
                        '_name': _prop_name,
                        '_type': _type,
                        '_default': _default,
                        '_enum': _enum
                    }

                    model['properties'].append(prop)

                #model['import_enum'] = True in ['enum' in p for p in model['properties']]
            
            self.definitions[model['name']] = model

    def write_file(self, filename):
        self.jinja.get_template(self.CLASS_TEMPLATE_FNAME).stream(models=self.definitions).dump(filename)

class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{} is not a readable dir".format(prospective_dir))

def init_parser():
    parser = argparse.ArgumentParser(description="Converts JSON Schema to Plain Old Python Object")
    parser.add_argument('json_schema_file', type=argparse.FileType('r', encoding='utf-8'), help="Path to JSON Schema file to load")
    parser.add_argument('-t', '--templates-folder', action=readable_dir, help="Path to templates folder", default=JsonSchema2Popo.TEMPLATES_FOLDER)
    parser.add_argument('-o', '--output-file', type=argparse.FileType('w', encoding='utf-8'), help="Path to file output", default="model.py")
    return parser

if __name__ == '__main__':
    parser = init_parser()
    args = parser.parse_args()

    loader = JsonSchema2Popo()
    loader.load(args.json_schema_file)

    outfile = args.output_file
    loader.write_file(outfile)
