#!/usr/bin/env python3

import os

import setuptools.command.test

NAME = 'django_celery_results'


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


setuptools.setup(
    packages=setuptools.find_packages(exclude=['ez_setup', 't', 't.*']),
    install_requires=reqs('default.txt'),
    tests_require=reqs('test.txt') + reqs('test-django.txt'),
    zip_safe=False,
    include_package_data=True,
)
