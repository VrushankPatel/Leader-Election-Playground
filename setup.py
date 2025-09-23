from setuptools import setup, find_packages

setup(
    name="leader-election-playground",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "grpcio==1.62.0",
        "grpcio-tools==1.62.0",
        "protobuf==4.25.0",
        "PyYAML==6.0.1",
        "rich==13.7.0",
        "aiohttp==3.9.1",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "lep-orchestrator=lep.orchestrator:main",
            "lep-node=lep.node:main",
            "lep-tui=lep.tui:main",
        ],
    },
)