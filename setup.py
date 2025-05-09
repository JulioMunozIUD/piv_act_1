from setuptools import setup, find_packages

setup(
    name='proyecto_nvidia',
    version='0.1.0',
    description='Descarga y almacenamiento de datos históricos de NVIDIA desde Yahoo Finance',
    author='Julio Muñoz',
    author_email='julio.munozr@est.iudigital.edu.co',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'requests',
        'beautifulsoup4',
        'pandas',
        'lxml'
    ],
    entry_points={
        'console_scripts': [
            'proyecto_nvidia=main:main',
        ],
    },
)