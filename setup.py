from setuptools import setup

setup(name='edward',
    version='0.1',
    description='A simple but extensible content management system for static wbesites. AKA static website generator.',
    url='http://github.com/ingokeck/edwardcms',
    author='Ingo Keck',
    author_email='ingokeck@ingokeck.de',
    license='AGPL',
    packages=['edward'],
    zip_safe=False,
    test_suite='nose.collector',
    test_require=['nose'],
    #scripts = ['bin/edward'],
    install_requires=['ruamel.yaml',
        'mako',
        'markdown'],
    entry_points = {'console_scripts': ['edward=edward.command_line:main']},
    include_package_data = True)
