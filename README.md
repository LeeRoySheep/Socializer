# Socializer 🚀

[![Python CI](https://github.com/yourusername/socializer/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/socializer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/socializer/graph/badge.svg?token=YOUR_TOKEN_HERE)](https://codecov.io/gh/yourusername/socializer)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern social AI chat application built with FastAPI, SQLAlchemy, and LangChain. Socializer provides an intelligent chat interface with user management, conversation history, and AI-powered responses.

## ✨ Features

- **User Authentication**: Secure JWT-based authentication with bcrypt password hashing
- **Encrypted Data**: All personal data (emails, passwords) encrypted with bcrypt, conversation memory encrypted with Fernet
- **Multi-Provider AI**: Support for OpenAI, Claude, Gemini, and local models (LM Studio/Ollama)
- **Automatic Language Detection**: AI-powered detection supporting 14+ languages
- **Social Skills Training**: Automated training system with progress tracking
- **Conversation History**: Encrypted conversation storage per user
- **RESTful API**: Built with FastAPI for high performance
- **Asynchronous**: Built with async/await for better performance
- **Comprehensive Tests**: 93%+ test coverage with pytest
- **Privacy-First**: Option for local AI processing (no data leaves your machine)

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL (or SQLite for development)
- OpenAI API key
- Tavily API key (for web search functionality)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/socializer.git
   cd socializer
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**
   ```bash
   pip install -e .[test,dev]  # For development with test and dev dependencies
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/socializer
   # or for SQLite: sqlite+aiosqlite:///./socializer.db
   
   # Security
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # OpenAI
   OPENAI_API_KEY=your-openai-api-key
   
   # Tavily (for web search)
   TAVILY_API_KEY=your-tavily-api-key
   ```

5. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   
   Explore the API documentation at `http://localhost:8000/docs`

## 🤖 AI Provider Comparison

Socializer supports multiple AI providers. We've tested them for **speed**, **cost**, and **quality**:

| Provider | Speed | Cost/Query | Quality | Best For |
|----------|-------|------------|---------|----------|
| **GPT-4o-mini** | 7.73s ⚡ | $0.0002 💵 | ⭐⭐⭐⭐ | **Production** (Fast + Cheap) |
| **Gemini 2.0 Flash** | 7.86s ⚡ | **FREE** 🎉 | ⭐⭐⭐⭐ | **Development** (No cost) |
| **Claude Sonnet 4.0** | 8.08s | $0.0036 💰 | ⭐⭐⭐⭐⭐ | **Premium** (Best quality) |
| **LM Studio (Local)** | 28.87s 🐌 | **FREE** 🎉 | ⭐⭐⭐ | **Privacy** (Offline) |

**Cost Comparison (1 million queries):**
- Gemini: $0 (FREE)
- GPT-4o-mini: $200
- Claude: $3,600 (18x more expensive!)

📊 **Detailed comparison**: See [AI_PROVIDER_COMPARISON.md](AI_PROVIDER_COMPARISON.md)

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=./ --cov-report=term-missing

# Run specific test file
pytest tests/test_chat_interface.py -v

# Run AI provider comparison
python tests/manual/ai_provider_real_comparison.py
```

## 🛠 Development

### Code Style

We use `black`, `isort`, and `flake8` for code formatting and linting:

```bash
# Format code
black .

# Sort imports
isort .

# Check for style issues
flake8
```

### Pre-commit Hooks

We use pre-commit to run checks before each commit. Install it with:

```bash
pre-commit install
```

This will automatically run the following checks before each commit:
- Remove trailing whitespace
- Check for large files
- Run black and isort
- Run flake8
- Run mypy type checking

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/socializer](https://github.com/yourusername/socializer)