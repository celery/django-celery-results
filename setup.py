#!/usr/bin/env python3

import codecs
import os
import re
import sys

import setuptools
import setuptools.command.test

try:
    import platform
    _pyimp = platform.python_implementation
except (AttributeError, ImportError):
    def _pyimp():
        return 'Python'

NAME = 'django_celery_results'

E_UNSUPPORTED_PYTHON = f'{NAME} 1.0 requires %s %s or later!'

PYIMP = _pyimp()
PY37_OR_LESS = sys.version_info < (3, 7)
PYPY_VERSION = getattr(sys, 'pypy_version_info', None)
PYPY73_ATLEAST = PYPY_VERSION and PYPY_VERSION >= (7, 3)

if PY37_OR_LESS and not PYPY73_ATLEAST:
    raise Exception(E_UNSUPPORTED_PYTHON % (PYIMP, '3.7'))

# -*- Classifiers -*-

classes = """
    Development Status :: 5 - Production/Stable
    License :: OSI Approved :: BSD License
    Programming Language :: Python
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.7
    Programming Language :: Python :: 3.8
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: Implementation :: CPython
    Programming Language :: Python :: Implementation :: PyPy
    Framework :: Django
    Framework :: Django :: 3.2
    Framework :: Django :: 4.0
    Operating System :: OS Independent
    Topic :: Communications
    Topic :: System :: Distributed Computing
    Topic :: Software Development :: Libraries :: Python Modules
"""
classifiers = [s.strip() for s in classes.split('\n') if s]

# -*- Distribution Meta -*-

re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
re_doc = re.compile(r'^"""(.+?)"""')


def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, attr_value.strip("\"'")),)


def add_doc(m):
    return (('doc', m.groups()[0]),)


pats = {re_meta: add_default,
        re_doc: add_doc}
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, NAME, '__init__.py')) as meta_fh:
    meta = {}
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))

# -*- Installation Requires -*-


def strip_comments(line):
    return line.split('#', 1)[0].strip()


def _pip_requirement(req):
    if req.startswith('-r '):
        _, path = req.split()
        return reqs(*path.split('/'))
    return [req]


def _reqs(*f):
    with open(os.path.join(os.getcwd(), 'requirements', *f)) as fp:
        return [
            _pip_requirement(r)
            for r in (strip_comments(line) for line in fp)
            if r
        ]


def reqs(*f):
    return [req for subreq in _reqs(*f) for req in subreq]

# -*- Long Description -*-


if os.path.exists('README.rst'):
    long_description = codecs.open('README.rst', 'r', 'utf-8').read()
else:
    long_description = f'See http://pypi.python.org/pypi/{NAME}'

# -*- %%% -*-


class pytest(setuptools.command.test.test):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to pytest')]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = []

    def run_tests(self):
        import pytest
        sys.exit(pytest.main(self.pytest_args))


setuptools.setup(
    name=NAME,
    packages=setuptools.find_packages(exclude=['ez_setup', 't', 't.*']),
    version=meta['version'],
    description=meta['doc'],
    long_description=long_description,
    long_description_content_type='text/x-rst',
    keywords='celery django database result backend',
    author=meta['author'],
    author_email=meta['contact'],
    url=meta['homepage'],
    platforms=['any'],
    license='BSD',
    classifiers=classifiers,
    install_requires=reqs('default.txt'),
    tests_require=reqs('test.txt') + reqs('test-django.txt'),
    cmdclass={'test': pytest},
    entry_points={
        'celery.result_backends': [
            'django-db = django_celery_results.backends:DatabaseBackend',
            'django-cache = django_celery_results.backends:CacheBackend',
        ],
    },
    zip_safe=False,
    include_package_data=True,
)
