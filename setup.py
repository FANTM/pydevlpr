from setuptools import setup, find_packages

VERSION = '0.1.0' 
DESCRIPTION = 'Connect to any FANTM device'
LONG_DESCRIPTION = 'Frontend for connecting to devlprd and processing data from a FANTM DEVLPR'

# Setting up
setup(
        name="pydevlpr-fantm", 
        version=VERSION,
        author="Ezra Boley",
        author_email="hello@getfantm.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        url='https://github.com/fantm/libdevlpr-plugin',
        packages=find_packages(where="src"),
        install_requires=['websockets'], # add any additional packages that 
        # needs to be installed along with your package.
        
        keywords=['python', 'FANTM', 'DEVLPR'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)