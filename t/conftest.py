import sys
import types
from contextlib import contextmanager
from unittest.mock import MagicMock, Mock, patch

import pytest

# we have to import the pytest plugin fixtures here,
# in case user did not do the `python setup.py develop` yet,
# that installs the pytest plugin into the setuptools registry.
from celery.contrib.pytest import (
    celery_app,
    celery_config,
    celery_enable_logging,
    celery_parameters,
    depends_on_current_app,
    use_celery_app_trap,
)
from celery.contrib.testing.app import TestApp, Trap

# Tricks flake8 into silencing redefining fixtures warnings.
__all__ = (
    'celery_app', 'celery_enable_logging', 'depends_on_current_app',
    'celery_parameters', 'celery_config', 'use_celery_app_trap'
)


SENTINEL = object()


@pytest.fixture(scope='session', autouse=True)
def setup_default_app_trap():
    from celery._state import set_default_app
    set_default_app(Trap())


@pytest.fixture()
def app(celery_app):
    return celery_app


@contextmanager
def module_context_manager(*names):
    """Mock one or modules such that every attribute is a :class:`Mock`."""
    yield from _module(*names)


def _module(*names):
    prev = {}

    class MockModule(types.ModuleType):

        def __getattr__(self, attr):
            setattr(self, attr, Mock())
            return types.ModuleType.__getattribute__(self, attr)

    mods = []
    for name in names:
        try:
            prev[name] = sys.modules[name]
        except KeyError:
            pass
        mod = sys.modules[name] = MockModule(name)
        mods.append(mod)
    try:
        yield mods
    finally:
        for name in names:
            try:
                sys.modules[name] = prev[name]
            except KeyError:
                try:
                    del sys.modules[name]
                except KeyError:
                    pass


class _patching:

    def __init__(self, monkeypatch, request):
        self.monkeypatch = monkeypatch
        self.request = request

    def __getattr__(self, name):
        return getattr(self.monkeypatch, name)

    def __call__(self, path, value=SENTINEL, name=None,
                 new=MagicMock, **kwargs):
        value = self._value_or_mock(value, new, name, path, **kwargs)
        self.monkeypatch.setattr(path, value)
        return value

    def object(self, target, attribute, *args, **kwargs):
        return _wrap_context(
            patch.object(target, attribute, *args, **kwargs),
            self.request)

    def _value_or_mock(self, value, new, name, path, **kwargs):
        if value is SENTINEL:
            value = new(name=name or path.rpartition('.')[2])
        for k, v in kwargs.items():
            setattr(value, k, v)
        return value

    def setattr(self, target, name=SENTINEL, value=SENTINEL, **kwargs):
        # alias to __call__ with the interface of pytest.monkeypatch.setattr
        if value is SENTINEL:
            value, name = name, None
        return self(target, value, name=name)

    def setitem(self, dic, name, value=SENTINEL, new=MagicMock, **kwargs):
        # same as pytest.monkeypatch.setattr but default value is MagicMock
        value = self._value_or_mock(value, new, name, dic, **kwargs)
        self.monkeypatch.setitem(dic, name, value)
        return value

    def modules(self, *mods):
        modules = []
        for mod in mods:
            mod = mod.split('.')
            modules.extend(reversed([
                '.'.join(mod[:-i] if i else mod) for i in range(len(mod))
            ]))
        modules = sorted(set(modules))
        return _wrap_context(module_context_manager(*modules), self.request)


def _wrap_context(context, request):
    ret = context.__enter__()

    def fin():
        context.__exit__(*sys.exc_info())
    request.addfinalizer(fin)
    return ret


@pytest.fixture()
def patching(monkeypatch, request):
    """Monkeypath.setattr shortcut.
    Example:
        .. code-block:: python
        >>> def test_foo(patching):
        >>>     # execv value here will be mock.MagicMock by default.
        >>>     execv = patching('os.execv')
        >>>     patching('sys.platform', 'darwin')  # set concrete value
        >>>     patching.setenv('DJANGO_SETTINGS_MODULE', 'x.settings')
        >>>     # val will be of type mock.MagicMock by default
        >>>     val = patching.setitem('path.to.dict', 'KEY')
    """
    return _patching(monkeypatch, request)


@pytest.fixture(autouse=True)
def test_cases_shortcuts(request, app, patching):
    if request.instance:
        @app.task
        def add(x, y):
            return x + y

        # IMPORTANT: We set an .app attribute for every test case class.
        request.instance.app = app
        request.instance.Celery = TestApp
        request.instance.add = add
        request.instance.patching = patching
    yield
    if request.instance:
        request.instance.app = None
