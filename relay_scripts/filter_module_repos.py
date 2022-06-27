#!/usr/bin/env python
from relay_sdk import Interface, Dynamic as D

relay = Interface()

modules = []
unsupported = []
incomplete = []

known = ['supported', 'trusted-contributor', 'maintenance-mode', 'community', 'education', 'experimental', 'demo']

for repo in relay.get(D.repositories):
    try:
        if 'module' in repo['topics']:
            full_name = 'puppetlabs/{0}'.format(repo['name'])
            modules.append(full_name)
            if not 'supported' in repo['topics']:
                unsupported.append(full_name)
            if len(set(known) & set(repo['topics'])) == 0:
                incomplete.append(full_name)

    except Exception as e:
        print('Could not process https://github.com/puppetlabs/{0}'.format(repo['name']))

relay.outputs.set('module_repos', modules)
relay.outputs.set('unsupported_module_repos', unsupported)
relay.outputs.set('incomplete_module_repos', incomplete)
