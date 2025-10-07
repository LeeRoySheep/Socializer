from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="socializer",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A social AI chat application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/socializer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.9",
    install_requires=[
        'fastapi>=0.95.0',
        'sqlalchemy>=2.0.0',
        'sqlmodel>=0.0.8',
        'uvicorn[standard]>=0.21.0',
        'python-dotenv>=1.0.0',
        'passlib>=1.7.4',
        'bcrypt>=4.0.0',
        'httpx>=0.24.0',
        'websockets>=11.0.0',
        'jinja2>=3.1.0',
        'python-multipart>=0.0.6',
        'python-jose[cryptography]>=3.3.0',
        'pyjwt>=2.6.0',
        'sqlalchemy-utils>=0.40.0',
        'alembic>=1.10.0',
        'openai>=0.27.0',
        'langchain>=0.0.200',
        'langchain-tavily>=0.0.1',
        'langgraph>=0.0.10',
        'anyio>=3.6.0',
        'nest-asyncio>=1.5.6',
        'requests>=2.28.0',
        'python-dateutil>=2.8.2',
        'typing-extensions>=4.5.0',
    ],
    extras_require={
        'test': [
            'pytest>=7.3.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'pytest-httpx>=0.24.0',
            'codecov>=2.1.12',
            'flake8>=6.0.0',
        ],
        'dev': [
            'black>=23.0.0',
            'isort>=5.12.0',
            'mypy>=1.0.0',
            'pre-commit>=3.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'socializer=app.main:main',
        ],
    },
)
