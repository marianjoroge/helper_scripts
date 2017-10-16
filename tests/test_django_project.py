from unittest.mock import call, patch
from pathlib import Path
import tempfile
from textwrap import dedent

import pythonanywhere.django_project
from pythonanywhere.django_project import DjangoProject



class TestDjangoProject:

    def test_project_path(self, fake_home):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        assert project.project_path == fake_home / 'mydomain.com'


    def test_wsgi_file_path(self, fake_home):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        assert project.wsgi_file_path == '/var/www/mydomain_com_wsgi.py'



class TestCreateVirtualenv:

    def xtest_calls_create_virtualenv_with_latest_django_by_default(self):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        with patch('pythonanywhere.django_project.create_virtualenv') as mock_create_virtualenv:
            project.create_virtualenv()
        assert mock_create_virtualenv.call_args == call(
            project.domain, python_version, 'django', nuke=False
        )


class TestRunStartproject:

    def test_creates_folder(self, mock_subprocess, fake_home):
        project = DjangoProject('mydomain.com', '/path/to/virtualenv')
        project.run_startproject(nuke=False)
        assert (fake_home / 'mydomain.com').is_dir()


    def test_calls_startproject(self, mock_subprocess, fake_home):
        DjangoProject('mydomain.com', '/path/to/virtualenv').run_startproject(nuke=False)
        assert mock_subprocess.check_call.call_args == call([
            Path('/path/to/virtualenv/bin/django-admin.py'),
            'startproject',
            'mysite',
            fake_home / 'mydomain.com',
        ])


    def test_nuke_option_deletes_directory_first(self, mock_subprocess, fake_home):
        domain = 'mydomain.com'
        (fake_home / domain).mkdir()
        old_file = fake_home / domain / 'old_file.py'
        with open(old_file, 'w') as f:
            f.write('old stuff')

        DjangoProject(domain, '/path/to/virtualenv').run_startproject(nuke=True)  # should not raise

        assert not old_file.exists()



class TestUpdateSettingsFile:

    def test_adds_STATIC_and_MEDIA_config_to_settings(self):
        project = DjangoProject('mydomain.com', 'ignored')
        project.project_path = Path(tempfile.mkdtemp())
        (project.project_path / 'mysite').mkdir(parents=True)
        with open(project.project_path / 'mysite/settings.py', 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.project_path / 'mysite/settings.py') as f:
            contents = f.read()

        lines = contents.split('\n')
        assert "STATIC_URL = '/static/'" in lines
        assert "MEDIA_URL = '/media/'" in lines
        assert "STATIC_ROOT = os.path.join(BASE_DIR, 'static')" in lines
        assert "MEDIA_ROOT = os.path.join(BASE_DIR, 'media')" in lines


    def test_adds_domain_to_ALLOWED_HOSTS(self):
        project = DjangoProject('mydomain.com', 'ignored')
        project.project_path = Path(tempfile.mkdtemp())
        (project.project_path / 'mysite').mkdir(parents=True)
        with open(project.project_path / 'mysite/settings.py', 'w') as f:
            f.write(dedent(
                """
                # settings file
                STATIC_URL = '/static/'
                ALLOWED_HOSTS = []
                """
            ))

        project.update_settings_file()

        with open(project.project_path / 'mysite/settings.py') as f:
            contents = f.read()

        lines = contents.split('\n')

        assert "ALLOWED_HOSTS = ['mydomain.com']" in lines



class TestRunCollectStatic:

    def test_runs_manage_py_in_correct_virtualenv(self, mock_subprocess, fake_home):
        domain, virtualenv = 'mydomain.com', '/path/to/virtualenv'
        project = DjangoProject(domain, virtualenv)
        project.run_collectstatic()
        assert mock_subprocess.check_call.call_args == call([
            Path(virtualenv) / 'bin/python', project.project_path / 'manage.py', 'collectstatic', '--noinput'
        ])



class TestUpdateWsgiFile:

    def test_updates_wsgi_file_from_template(self):
        domain, virtualenv = 'mydomain.com', '/path/to/virtualenv'
        project = DjangoProject(domain, virtualenv)
        project.wsgi_file_path = tempfile.NamedTemporaryFile().name
        template = open(Path(pythonanywhere.django_project.__file__).parent / 'wsgi_file_template.py').read()

        project.update_wsgi_file()

        with open(project.wsgi_file_path) as f:
            contents = f.read()
        assert contents == template.format(project_path=project.project_path)

