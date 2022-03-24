import setuptools


with open('README.md') as f:
    long_description = f.read()


setuptools.setup(
    name='m3u8',
    version='0.0.1',
    author='WaizungTaam',
    author_email='waizungtaam@gmail.com',
    license='MIT',
    description='Python m3u8 parser',
    long_description=long_description,
    packages=['m3u8'],
    include_package_data=True,
    install_requires=[
        'python-dateutil',
    ],
    extras_require={},
    python_requires='>=3.6',
)
