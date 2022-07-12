#!/usr/bin/env python
import re
from urllib import request
from jinja2 import Template
from relay_sdk import Interface, Dynamic as D

relay = Interface()

modules = relay.get(D.modules)
repositories = relay.get(D.repositories)
unmarked = relay.get(D.unmarked)
incomplete = relay.get(D.incomplete)

tag_module = []
badge_supported = []
badge_unsupported = []
source_field_problem = []
badge_adoptable = []

for mod in modules:
    try:
        reponame = re.search('github\.com[/:]puppetlabs\/([\w-]*)', mod['metadata']['source']).group(1)
        repo = next(x for x in repositories if x['name'] == reponame)

        if not 'module' in repo['topics']:
            tag_module.append(repo)

        if mod['endorsement'] != 'supported' and 'supported' in repo['topics']:
            badge_supported.append(mod)

        if mod['endorsement'] == 'supported' and not 'supported' in repo['topics']:
            badge_unsupported.append(mod)

    except (AttributeError, StopIteration) as e:
        try:
            # try opening the URL just to follow any redirects
            r = request.urlopen('https://github.com/puppetlabs/{0}'.format(reponame))
            if re.search('toy-chest', r.geturl()):
                badge_adoptable.append(mod)
            else:
                source_field_problem.append(mod)
        except Exception as e:
            source_field_problem.append(mod)

    except Exception as e:
        print('Could not process module {0}'.format(mod['slug']))

template = """# Module Repository Housekeeping Audit

The following modules are out of compliance with our module support policy. Each
repository should have a topic and a `README` note describing its support tier and
should have a `CODEOWNERS` file identifying the engineering team responsible for it.
See <not yet published> for details.

----

{%- if tag_module -%}
## Missing `module` topic:

The following GitHub repositories were detected as Puppet modules, but are missing the 'module' topic:

{%- for item in tag_module %}
* [puppetlabs/{{ item['name'] }}](https://github.com/puppetlabs/{{ item['name'] }})
{%- endfor %}
{%- endif %}
{%- if incomplete %}


## Missing support tier topic:

The following GitHub repositories should have topics clarifying which support tier they fall into.

{%- for item in incomplete %}
* [{{ item }}](https://github.com/{{ item }})
{%- endfor %}
{%- endif %}
{%- if unmarked %}


## Missing README preamble:

The following GitHub repositories do not have a properly formatted README preamble
explaining what kind of support a user can expect from a module.

{%- for item in unmarked %}
* [{{ item }}](https://github.com/{{ item }})
{%- endfor %}
{%- endif %}
{%- if badge_supported %}


## Add Supported badge

The following Forge modules should be badged as Supported:

{%- for item in badge_supported %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{%- endfor %}
{%- endif %}
{%- if badge_unsupported %}


## Remove Supported badge

The following Forge modules should have the Supported badge removed:

{%- for item in badge_unsupported %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{%- endfor %}
{%- endif %}
{%- if badge_adoptable %}


## Add Adoptable badge

The repositories for these modules have been archived into the Toy Chest and
should be badged as Adoptable:

{%- for item in badge_adoptable %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{%- endfor %}
{%- endif %}
{%- if source_field_problem %}


## Source field problem

The following Forge modules have a problem with their source field. Either the
field could not be parsed, or it does not point to a valid public repo within the org.

{%- for item in source_field_problem %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{%- endfor %}
{%- endif %}
"""

tm = Template(template)
report = tm.render(tag_module=tag_module, badge_supported=badge_supported, badge_unsupported=badge_unsupported, badge_adoptable=badge_adoptable, source_field_problem=source_field_problem, unmarked=unmarked, incomplete=incomplete)

relay.outputs.set('report', report)
