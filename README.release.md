Making a Release
================

1. Commit all other changes
2. Update the version string in both places:
   - motifapi/__init__.py  (__version__ = '0.2.X')
   - setup.py              (version='0.2.X')
3. Commit the version change: git commit -am "0.2.X"
4. Create a tag: git tag -a v0.2.X -m "0.2.X"
5. Push the commit and tag together: git push origin master --tags --atomic

The CI workflow builds an sdist+wheel and publishes to PyPI on any
tag push matching v*. Deb packages are also built for matching tags.
