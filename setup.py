import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '0.0.4'

if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()

setup(
    name='django-cloud-tasks',
    version=version,
    description="""Google Cloud Tasks integration for Django""",
    long_description=readme,
    author='GeorgeLubaretsi',
    url='https://github.com/GeorgeLubaretsi/django-cloud-tasks',
    packages=[
        'django_cloud_tasks',
    ],
    include_package_data=True,
    install_requires=[
        'google-api-python-client>=1.6.4',
    ],
    license="MIT",
    zip_safe=False,
    keywords='django cloudtasks cloud tasks',
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
