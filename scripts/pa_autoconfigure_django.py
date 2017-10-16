#!/usr/bin/python3.6
"""Autoconfigure a Django project from on a github URL.

- downloads the repo
- creates a virtualenv and installs django (or detects a requirements.txt if available)
- creates webapp via api
- creates django wsgi configuration file
- adds static files config

Usage:
  pa_autoconfigure_django.py <git-repo-url> [--domain=<domain> --python=<python-version>] [--nuke]

Options:
  --domain=<domain>         Domain name, eg www.mydomain.com   [default: your-username.pythonanywhere.com]
  --python=<python-version> Python version, eg "2.7"    [default: 3.6]
  --nuke                    *Irrevocably* delete any existing web app config on this domain. Irrevocably.
"""

from docopt import docopt
import getpass
from pathlib import Path
import subprocess
import shutil

from pythonanywhere.sanity_checks import sanity_checks
from pythonanywhere.virtualenvs import create_virtualenv
from pythonanywhere.api import create_webapp
from pythonanywhere.django_project import DjangoProject


def download_repo(repo, domain, nuke):
    target = Path('~').expanduser() / domain
    if nuke:
        shutil.rmtree(target)
    subprocess.check_call(['git', 'clone', repo, target])
    return target

def main(repo_url, domain, python_version, nuke):
    if domain == 'your-username.pythonanywhere.com':
        username = getpass.getuser().lower()
        domain = f'{username}.pythonanywhere.com'

    sanity_checks(domain, nuke=nuke)
    project_path = download_repo(repo_url, domain, nuke=nuke)
    virtualenv = create_virtualenv(domain, python_version, nuke=nuke)


    create_webapp(domain, python_version, virtualenv, project_path, nuke=nuke)

    project = DjangoProject(domain, virtualenv)
    project.update_wsgi_file()
    project.update_settings_file()
    project.run_collectstatic()
    # run_collectstatic(virtualenv_path, project_path)
    # add_static_file_mappings(domain, project_path)
    # reload_webapp(domain)

    # print(snakesay(f'All done!  Your site is now live at https://{domain}'))





if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<git-repo-url>'], arguments['--domain'], arguments['--python'], nuke=arguments.get('--nuke'))
