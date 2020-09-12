import setuptools

setuptools.setup(
    name='qspreadsheet',
    version='0.1.0',
    author='TT-at-GitHub',
    author_email='tt3d@start.bg',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy>=1.19.0',
        'pandas>=1.0.5',
        'PySide2>=5.13.0'
    ],
    description='Package used to show and edit pandas DataFrame in GUI',
    python_requires='>=3.7.5'
)