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

# this doesn't really fit here, but for now...
unowned = relay.get(D.unowned)

tag_module = []
badge_supported = []
badge_unsupported = []
source_field_problem = []
badge_adoptable = []

premium_content = [ 'cem_linux', 'cem_windows' ]

for mod in modules:
    if mod['deprecated_at']:
        continue

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
        if reponame in premium_content:
            continue

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

template = """# Open Source Housekeeping Audit

Puppet's Open Source Stewards group conducts a regular audit of our public GitHub
namespace and our Puppet Forge namespace for modules and repositories that do not
meet our standards and policies. This report contains content which is out of
compliance and should be either removed or corrected.

Each section below describes expectations for a check and suggestions for remediating
the failure. Expand the list to see all the content that failed the check.

If a repository is no longer useful then remove it rather than working to make it
compliant.

* If anyone else might find practical use or learning opportunities, then bin
  the repository into the [Toy Chest](http://github.com/puppetlabs-toy-chest/)
  to mark it as adoptable.
* If the repository has no use to anyone, then simply delete it.

See `{not yet published}` for details about our housekeeping standards.

----

{% if tag_module -%}
## GitHub: Module repository missing `module` topic

<details>
<summary>
Module repositories should be indicated with the `module` topic. The following
repositories were detected as Puppet modules, but are missing that topic.
</summary>

{% for item in tag_module -%}
* [puppetlabs/{{ item['name'] }}](https://github.com/puppetlabs/{{ item['name'] }})
{% endfor -%}
</details>
{% endif -%}


{% if incomplete -%}
## GitHub: Module repositories missing support tier topic

<details>
<summary>
Modules in the Puppetlabs namespace have different support expectations. Each module
repository should have a topic identifying which support tier it falls into. The
following GitHub repositories are missing their support tier topics and should
have them added.
</summary>

{% for item in incomplete -%}
* [{{ item }}](https://github.com/{{ item }})
{% endfor -%}
</details>
{% endif -%}


{% if unmarked -%}
## GitHub: Module repositories missing README preamble

<details>
<summary>
Modules in the Puppetlabs namespace have different support expectations. Each module
should have a properly formatted `README` preamble explaining what kind of support
a user can expect when using that module.

The following GitHub repositories should have a preamble added to their `README`.
</summary>

{% for item in unmarked -%}
* [{{ item }}](https://github.com/{{ item }})
{% endfor -%}
</details>
{%- endif %}


{% if unowned -%}
## GitHub: Invalid CODEOWNERS files

<details>
<summary>

All public repositories in the `puppetlabs` namespace should have valid `CODEOWNERS`
clearly showing ownership and responsibilities. This allows us to automatically
assign pull request reviews and makes it easier to identify teams responsible for
a project.

The following GitHub repositories have problems with their `CODEOWNERS` files. Click
through to inspect the errors using GitHub's interface and it will offer suggestions
on how to resolve problems.
</summary>

{% for item in unowned -%}
* [puppetlabs-{{ item }}](https://github.com/puppetlabs/{{ item }}/blob/-/CODEOWNERS)
{% endfor -%}
</details>
{% endif -%}


{% if badge_supported -%}
## Forge: Add Supported badge

<details>
<summary>
Forge module pages should match the topics on their corresponding repositories.
The following Forge modules should be badged as Supported.
</summary>

{% for item in badge_supported -%}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{% endfor -%}
</details>
{% endif -%}


{% if badge_unsupported -%}
## Forge: Remove Supported badge

<details>
<summary>
Forge module pages should match the topics on their corresponding repositories.
The following Forge modules should have the Supported badge removed.
</summary>

{%- for item in badge_unsupported %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{% endfor -%}
</details>
{% endif -%}


{% if badge_adoptable -%}
## Forge: Add Adoptable badge
<details>
<summary>
The repositories for these modules have been archived into the Toy Chest, so their
Forge pages should be badged as `Adoptable`.
</summary>

{%- for item in badge_adoptable %}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{% endfor -%}
</details>
{% endif -%}


{% if source_field_problem -%}
## Forge: Source field problem

<details>
<summary>
Our standards for the `source` key in `metadata.json` is to point to the HTML url
of the GitHub repository containing module source. The following Forge modules do
not match that expectation. Either the field could not be parsed, or it does not
point to a valid public repo within the org. Sometimes this happens when another
developer takes ownership of a module and the Forge page isn't updated to match.

Correct the field for any modules we own, and deprecate as appropriate any modules
we no longer own.
</summary>

{% for item in source_field_problem -%}
* [puppetlabs-{{ item['name'] }}](https://forge.puppet.com/puppetlabs/{{ item['name'] }})
{% endfor -%}
</details>
{% endif -%}
"""

tm = Template(template)
report = tm.render(tag_module=tag_module, badge_supported=badge_supported, badge_unsupported=badge_unsupported, badge_adoptable=badge_adoptable, source_field_problem=source_field_problem, unmarked=unmarked, incomplete=incomplete, unowned=unowned)

relay.outputs.set('report', report)
