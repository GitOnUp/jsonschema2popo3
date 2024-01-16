import json
import os

import networkx
from jinja2 import Environment, FileSystemLoader

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class Generator:
    """Converts a JSON Schema to a Plain Old Python Object class"""

    CLASS_TEMPLATE_FNAME = "_class.jinja"

    J2P_TYPES = {
        "string": str,
        "integer": int,
        "number": float,
        "object": type,
        "array": list,
        "boolean": bool,
        "null": None,
    }

    def __init__(self):
        self.jinja = Environment(
            loader=FileSystemLoader(searchpath=SCRIPT_DIR), trim_blocks=True
        )

        self.definitions = []

    def load(self, json_schema_file):
        self.process(json.load(json_schema_file))

    def get_model_depencencies(self, model):
        deps = set()
        for prop in model["properties"]:
            if prop["_type"]["type"] not in self.J2P_TYPES.values():
                deps.add(prop["_type"]["type"])
            if prop["_type"]["subtype"] not in self.J2P_TYPES.values():
                deps.add(prop["_type"]["subtype"])
        return list(deps)

    def process(self, json_schema):
        for _obj_name, _obj in json_schema["definitions"].items():
            model = self.definition_parser(_obj_name, _obj)
            self.definitions.append(model)

        # topological oderd dependencies
        g = networkx.DiGraph()
        models_map = {}
        for model in self.definitions:
            models_map[model["name"]] = model
            deps = self.get_model_depencencies(model)
            if not deps:
                g.add_edge(model["name"], "")
            for dep in deps:
                g.add_edge(model["name"], dep)

        self.definitions = []
        for model_name in list(reversed(list(networkx.topological_sort(g)))):
            if model_name in models_map:
                self.definitions.append(models_map[model_name])

        # root object
        if "title" in json_schema:
            root_object_name = "".join(
                x for x in json_schema["title"].title() if x.isalpha()
            )
        else:
            root_object_name = "RootObject"
        root_model = self.definition_parser(root_object_name, json_schema)
        self.definitions.append(root_model)

    def definition_parser(self, _obj_name, _obj):
        model = {}
        model["name"] = _obj_name
        if "type" in _obj:
            model["type"] = self.type_parser(_obj)

        def get_python_type_hint(prop: dict):
            # TODO #7 Add Optional here for not required types
            hint = None
            prop_type = prop["_type"]["type"]
            prop_subtype = prop["_type"]["subtype"]
            prop_format = prop["_format"]
            if isinstance(prop_type, str):
                # Name of a type
                hint = prop_type
            elif prop_type == list:
                if isinstance(prop_subtype, str):
                    hint = f"[{prop_subtype}]"
                else:
                    hint = f"[{prop_subtype.__name__}]"
            elif prop_type == str:
                if prop_format == "date-time":
                    hint = "datetime"
                else:
                    hint = "str"
            elif prop_type is None:
                hint = "None"
            else:
                assert type(prop_type) == type
                hint = prop_type.__name__
            return hint

        model["properties"] = []
        if "properties" in _obj:
            for _prop_name, _prop in _obj["properties"].items():
                _type = self.type_parser(_prop)
                _default = None
                if "default" in _prop:
                    _default = _type["type"](_prop["default"])
                    if _type["type"] == str:
                        _default = "'{}'".format(_default)

                _enum = None
                if "enum" in _prop:
                    _enum = _prop["enum"]

                _format = None
                if "format" in _prop:
                    _format = _prop["format"]
                if (
                    _type["type"] == list
                    and "items" in _prop
                    and isinstance(_prop["items"], list)
                ):
                    _format = _prop["items"][0]["format"]

                prop = {
                    "_name": _prop_name,
                    "_type": _type,
                    "_default": _default,
                    "_enum": _enum,
                    "_format": _format,
                }
                prop["_type_hint"] = get_python_type_hint(prop)
                model["properties"].append(prop)
        return model

    def type_parser(self, t):
        _type = None
        _subtype = None
        if "type" in t:
            if t["type"] == "array" and "items" in t:
                _type = self.J2P_TYPES[t["type"]]
                if isinstance(t["items"], list):
                    if "type" in t["items"][0]:
                        _subtype = self.J2P_TYPES[t["items"][0]["type"]]
                    elif (
                        "$ref" in t["items"][0]
                        or "oneOf" in t["items"][0]
                        and len(t["items"][0]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"][0]:
                            ref = t["items"][0]["$ref"]
                        else:
                            ref = t["items"][0]["oneOf"][0]["$ref"]
                        _subtype = ref.split("/")[-1]
                elif isinstance(t["items"], dict):
                    if "type" in t["items"]:
                        _subtype = self.J2P_TYPES[t["items"]["type"]]
                    elif (
                        "$ref" in t["items"]
                        or "oneOf" in t["items"]
                        and len(t["items"]["oneOf"]) == 1
                    ):
                        if "$ref" in t["items"]:
                            ref = t["items"]["$ref"]
                        else:
                            ref = t["items"]["oneOf"][0]["$ref"]
                        _subtype = ref.split("/")[-1]
            elif isinstance(t["type"], list):
                _type = self.J2P_TYPES[t["type"][0]]
            elif t["type"]:
                _type = self.J2P_TYPES[t["type"]]
        elif "$ref" in t:
            _type = t["$ref"].split("/")[-1]
        elif "anyOf" in t or "allOf" in t or "oneOf" in t:
            _type = list
        return {"type": _type, "subtype": _subtype}

    def write_file(self, filename):
        self.jinja.get_template(self.CLASS_TEMPLATE_FNAME).stream(
            models=self.definitions
        ).dump(filename)
