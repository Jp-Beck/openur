from setuptools import setup, find_packages

setup(
    name='OpenUr',
    version='0.2.4',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'openur = openur.cli:main',
        ],
    },
    py_modules=['openur'],
    install_requires=[
        'numpy',
        'math3d',
        'ikpy'  
    ],
    author='Beck Isakov',
    author_email='jp-beck@outlook.com',
    description='All in one package for complete control of your UR robot.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/Jp-Beck',
    provides=["openur"],  
    license="GNU GPLv3 License",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',  
        'Intended Audience :: Developers',  
        'Operating System :: OS Independent',  
        'Topic :: System :: Hardware :: Hardware Drivers',  
        'Topic :: Software Development :: Libraries :: Python Modules',  
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
)