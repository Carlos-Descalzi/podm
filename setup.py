import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="podm",
    version="0.0.10.1",
    author="Carlos Descalzi",
    author_email="carlos.descalzi@gmail.com",
    description="A Object-JSON Document mapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Carlos-Descalzi/podm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
