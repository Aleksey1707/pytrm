from typing import List

from setuptools import find_packages, setup

import pytrm


def long_description() -> str:
    with open("README.md", encoding="utf-8") as f:
        return f.read()


def install_requires() -> List[str]:
    with open("requirements.txt") as f:
        return f.readlines()


assert pytrm.__doc__ is not None


setup(
    name="pytrm",
    version=pytrm.__version__,
    description=pytrm.__doc__.strip(),
    long_description=long_description(),
    long_description_content_type="text/markdown",
    author=pytrm.__author__,
    author_email="AlekseyOdi@yandex.ru",
    license=pytrm.__license__,
    packages=find_packages(),
    include_package_data=True,
    package_data={"pytrm": ["py.typed"]},
    python_requires=">=3.9,<4.0",
    install_requires=install_requires(),
    extras_require={
        "mongo-motor": ["motor>=3"],
        "sqlalchemy": ["SQLAlchemy>=2"],
    },
)
