#!/usr/bin/env python
import os
import sys
import importlib.util
import subprocess as sp
from pathlib import Path
import shutil
from typing import Union

# https://stackoverflow.com/a/9562273/54557
# Doesn't write __pycache__ files.
sys.dont_write_bytecode = True


def load_module(local_filename: Union[str, Path]):
    """Use Python internals to load a Python module from a filename.

    :param local_filename: name of module to load
    :return: module
    """
    module_path = Path.cwd() / local_filename
    if not module_path.exists():
        raise Exception(f'Module file {module_path} does not exist')

    # No longer needed due to sys.modules line below.
    # Make sure any local imports in the module script work.
    sys.path.append(str(module_path.parent))
    module_name = Path(local_filename).stem

    try:
        # See: https://stackoverflow.com/a/50395128/54557
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except SyntaxError:
        print(f'Bad syntax in module file {module_path}')
        raise

    return module


def runcmd(cmd):
    return sp.run(cmd, shell=True, stdout=sp.PIPE, check=True, encoding='utf8')


def main():
    settings = load_module('publish_settings.py').SETTINGS
    user_prompt = settings['user_prompt']
    # print(settings)
    destinations = settings['destinations'].keys()
    if settings.get('force_make', True):
        if not os.getenv('MAKELEVEL'):
            print('Not being called with make, exiting')
            sys.exit(1)
    git_status = runcmd('git status --porcelain').stdout
    if git_status:
        if not settings.get('git_allow_uncommitted', False):
            print('Uncommitted changes! Cannot run')
            print(git_status)
            sys.exit(1)
        else:
            print('WARNING: Uncommitted changes.')
            print(git_status)
    destination = sys.argv[1]
    assert destination in destinations, f'Destination "{destination}" not in {destinations}'

    if settings['version_format'] == 'git_describe':
        try:
            version = runcmd('git describe --tags').stdout.strip()
        except sp.CalledProcessError as e:
            print('No tags found -- add a tag with "git tag"')
            sys.exit(1)
    elif settings['version_format'] == 'user_supplied':
        version = sys.argv[2]

    dsettings = settings['destinations'][destination]
    files = dsettings['files']
    paths = []
    for source_path_tpl, target_path_tpl in [(f['source'], f['target']) for f in files]:
        source_path = Path(source_path_tpl.format(destination=destination, version=version)).expanduser()
        target_path = Path(target_path_tpl.format(destination=destination, version=version)).expanduser()
        if not settings.get('overwrite', False):
            assert not target_path.exists(), '{} already exists'.format(target_path)
        paths.append((source_path, target_path))

    for source_path, target_path in paths:
        r = input('Create new file: {} (y/[n]): '.format(target_path)) if user_prompt else 'y'
        if r.lower() in ['y', 'yes']:
            target_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(source_path, str(target_path))
            print('Created file: {}'.format(target_path))

    if settings['archive']:
        asettings = settings['archive']
        archive_path = Path(asettings['target'].format(destination=destination, version=version)).expanduser()
        archive_format = asettings['format']
        prefix = asettings['prefix']
        branch = asettings['branch']
        r = input('Create archive file: {} (y/[n]): '.format(archive_path)) if user_prompt else 'y'
        if r.lower() in ['y', 'yes']:
            archive_path.parent.mkdir(exist_ok=True, parents=True)
            cmd = f'git archive --format={archive_format} --prefix="{prefix}" -o {archive_path} {branch}'
            runcmd(cmd)
            print('Created archive: {}'.format(archive_path))


if __name__ == '__main__':
    main()

