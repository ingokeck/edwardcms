from setuptools import setup

setup(name='edward',
    version='0.1.0b',
    description='A simple but extensible content management system for static websites. AKA static website generator.',
    url='http://github.com/ingokeck/edwardcms',
    author='Ingo Keck',
    author_email='ingokeck@ingokeck.de',
    license='AGPLv3+',
    packages=['edward'],
    zip_safe=False,
    test_suite='nose.collector',
    test_require=['nose'],
    #scripts = ['bin/edward'],
    install_requires=['ruamel.yaml',
        'mako',
        'markdown'],
    entry_points = {'console_scripts': ['edward=edward.command_line:main']},
    include_package_data = True,
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Site Management',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.5',
        ],
      )
