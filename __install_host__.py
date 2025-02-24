from venv import create
from os.path import join, abspath
from subprocess import run
from os.path import join, abspath, dirname

def create_venv(path: str = ".venv", path_to_requirements_txt: str = None) -> None:
    create(path, system_site_packages=True, with_pip=True)

    if path_to_requirements_txt is None:
        return
    print(f". {join(path, 'bin', 'activate')} && pip install --prefer-binary -r {path_to_requirements_txt}")
    run(f". {join(path, 'bin', 'activate')} && pip install --prefer-binary -r {path_to_requirements_txt}", start_new_session=True, shell=True)

toplevel = dirname(abspath(__file__))
create_venv(join(toplevel, "backend", ".venv"), join(toplevel, "backend", "requirements.txt"))