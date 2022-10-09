# coding:utf8
from setuptools import setup, find_packages
from pathlib import Path

with open("./README.md", encoding="utf-8") as ff:
    readme_text = ff.read()

# Parse version
init = Path(__file__).parent.joinpath("consign", "__init__.py")
for line in init.read_text(encoding="utf-8").split("\n"):
    if line.startswith("__version__ ="):
        break
version = line.split(" = ")[-1].strip('"')

setup(
    name='pyconsign',         # 应用名
    version=version,        # 版本号
    long_description_content_type="text/markdown",
    long_description=readme_text,
    packages=find_packages(),
    install_requires=[    # 依赖列表
        'contextvars;python_version<"3.7"',
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires=">=3.5",
    author="SpectrePrediction",
    author_email="1007108187@qq.com",
    description="Generator-based Coroutines, Easy to use, Using the yield syntax",
    keywords=["coroutines", "generator", "yield"],
    url="https://github.com/SpectrePrediction/consign",   # 项目主页
    license="MIT License",
)