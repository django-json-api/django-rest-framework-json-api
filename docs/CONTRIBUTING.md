Contributing
============

DJA should be easy to contribute to.
If anything is unclear about how to contribute,
please submit an issue on GitHub so that we can fix it!

How
---

Before writing any code,
have a conversation on a GitHub issue
to see if the proposed change makes sense
for the project.

Fork DJA on [GitHub](https://github.com/django-json-api/django-rest-framework-json-api) and
[submit a Pull Request](https://help.github.com/articles/creating-a-pull-request/)
when you're ready.

For maintainers
---------------

To upload a release (using version 1.2.3 as the example):

```bash
(venv)$ python setup.py sdist bdist_wheel
(venv)$ twine upload dist/*
(venv)$ git tag -a v1.2.3 -m 'Release 1.2.3'
(venv)$ git push --tags
```
