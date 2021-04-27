from invoke import task, run


@task
def test(c):
    run('nose2 -v --pretty-assert --output-buffer --fail-fast --with-coverage --coverage-report term')
    run('coverage report -m')


@task
def load(c):
    run('pip install -e .')


@task
def code(c):
    run('black src/*/*.py')
    run('black tests/*.py')
    run('isort src/*/*.py')
    run('isort tests/*.py')
    run('flake8 --max-complexity 8 src/*/*.py')
    run('pycodestyle src/*/*py')
    run('mypy src/*/*.py')


@task
def mypy(c):
    run('mypy src/*/*.py')
