# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections
import logging
import os

import jinja2
from jinja2 import meta
import six
import yaml

from kolla_k8s.common import type_utils

LOG = logging.getLogger(__name__)


# Customize PyYAML library to return the OrderedDict. That is needed, because
# when iterating on dict, we reuse its previous values when processing the
# next values and the order has to be preserved.

def ordered_dict_constructor(loader, node):
    """OrderedDict constructor for PyYAML."""
    return collections.OrderedDict(loader.construct_pairs(node))


def ordered_dict_representer(dumper, data):
    """Representer for PyYAML which is able to work with OrderedDict."""
    return dumper.represent_dict(data.items())


yaml.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                     ordered_dict_constructor)
yaml.add_representer(collections.OrderedDict, ordered_dict_representer)


def jinja_render(fullpath, global_config, extra=None):
    variables = global_config
    if extra:
        variables.update(extra)

    myenv = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            os.path.dirname(fullpath)))
    myenv.filters['bool'] = type_utils.str_to_bool
    return myenv.get_template(os.path.basename(fullpath)).render(variables)


def jinja_render_str(content, global_config, name='dafault_name', extra=None):
    variables = global_config
    if extra:
        variables.update(extra)

    myenv = jinja2.Environment(loader=jinja2.DictLoader({name: content}))
    myenv.filters['bool'] = type_utils.str_to_bool
    return myenv.get_template(name).render(variables)


def jinja_find_required_variables(fullpath):
    myenv = jinja2.Environment(loader=jinja2.FileSystemLoader(
        os.path.dirname(fullpath)))
    myenv.filters['bool'] = type_utils.str_to_bool
    template_source = myenv.loader.get_source(myenv,
                                              os.path.basename(fullpath))[0]
    parsed_content = myenv.parse(template_source)
    return meta.find_undeclared_variables(parsed_content)


def dict_jinja_render(raw_dict, jvars):
    """Renders dict with jinja2 using provided variables and itself.

    By using itself, we mean reusing the previous values from dict for the
    potential render of the next value in dict.
    """
    for key, value in raw_dict.items():
        if isinstance(value, six.string_types):
            value = jinja_render_str(value, jvars)
        elif isinstance(value, dict):
            value = dict_jinja_render(value, jvars)
        jvars[key] = value


def yaml_jinja_render(filename, jvars):
    """Parses YAML file and templates it with jinja2.

    1. YAML file is rendered by jinja2 based on the provided variables.
    2. Rendered file is parsed.
    3. The every element dictionary being a result of parsing is rendered again
       with itself.
    """
    with open(filename, 'r') as yaml_file:
        raw_dict = yaml.load(yaml_file)
    dict_jinja_render(raw_dict, jvars)
