import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
     name='ciscocfg',
     version='0.1',
     scripts=['ciscocfgd'],
     author="Mareel Team",
     author_email="admin@mareel.io",
     description="Cisco configuration manipulation daemon",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/mareel-io/ciscocfg",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: GPL 3.0",
         "Operating System :: OS Independent",
     ],
 )
