from venv import create
from os.path import join, abspath, isfile
import subprocess
from os.path import join, abspath, dirname

def create_venv(path: str = ".venv", path_to_requirements_txt: str = None) -> None:
    create(path, system_site_packages=True, with_pip=True)

    if path_to_requirements_txt is None:
        return
    print(f". {join(path, 'bin', 'activate')} && pip install --prefer-binary -r {path_to_requirements_txt}")
    run(f". {join(path, 'bin', 'activate')} && pip install --prefer-binary -r {path_to_requirements_txt}",
        start_new_session=True, shell=True)

toplevel = dirname(abspath(__file__))
if isfile("/.flatpak-info"):
    install_script = join(toplevel, "__install_host__.py")
    process = subprocess.Popen(f"flatpak-spawn --directory {toplevel} --host python {install_script}")
else:
    create_venv(join(toplevel, "backend", ".venv"), join(toplevel, "requirements.txt"))

#toplevel = dirname(abspath(__file__))
#venv, requirements = join(toplevel, "backend", ".venv"), join(toplevel, "requirements.txt")