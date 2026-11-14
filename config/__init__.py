# Python 3.15 + Django 5.1 compatibility patch for BaseContext.__copy__
from django.template import context as django_context


def _patched_base_context_copy(self):
    duplicate = object.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate


django_context.BaseContext.__copy__ = _patched_base_context_copy

