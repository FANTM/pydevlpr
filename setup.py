from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Connect to any FANTM device'
LONG_DESCRIPTION = 'Glue to attach any application to a FANTM device over websockets'

# Setting up
setup(
       # the name must match the folder name 'verysimplemodule'
        name="libdevlpr", 
        version=VERSION,
        author="Ezra Boley",
        author_email="hello@getfantm.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['asyncio', 'websockets'], # add any additional packages that 
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