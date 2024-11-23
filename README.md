# AI Agent Management System

A scalable system for managing, monitoring, and orchestrating AI agents built with FastAPI, LangChain, and SQLite.

## 🚀 Features

- **Agent Management**
  - Create and configure AI agents
  - Start/stop agent execution
  - Monitor agent status and performance
  - Real-time updates via WebSocket

- **Task Execution**
  - Assign tasks to agents
  - Track task progress
  - Store execution history
  - Handle errors and retries

- **Resource Management**
  - Database persistence
  - Memory management
  - Tool integration
  - State tracking

## 🛠️ Technical Stack

- **Backend**: FastAPI
- **Database**: SQLite
- **AI Framework**: LangChain
- **LLM Integration**: OpenAI
- **API Documentation**: Swagger/OpenAPI

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key
- Virtual environment management

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-agent-manager.git
cd ai-agent-manager
```

2. Create and activate virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate
# Activate (Windows)
# venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
# .env
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///agents.db
API_HOST=127.0.0.1
API_PORT=8000
```

## 🚀 Running the Application

1. Start the server:
```bash
python run.py
```

2. Access the API documentation:
```
http://127.0.0.1:8000/docs
```

## 📖 API Documentation

### Endpoints

#### Agents
- `POST /api/v1/agents/` - Create a new agent
- `POST /api/v1/agents/{agent_id}/start` - Start an agent
- `POST /api/v1/agents/{agent_id}/stop` - Stop an agent
- `GET /api/v1/agents/{agent_id}` - Get agent status

#### Tasks
- `POST /api/v1/agents/{agent_id}/tasks` - Execute a task

#### WebSocket
- `WS /api/v1/ws/agents/{agent_id}` - Real-time agent updates

### Example Usage

```python
# Create an agent
POST /api/v1/agents/
{
    "name": "research_agent",
    "config": {
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.7
    }
}

# Execute a task
POST /api/v1/agents/{agent_id}/tasks
{
    "type": "research",
    "input": "What are the latest developments in AI?"
}
```

## 🗄️ Project Structure

```
aim/
├── src/
│   ├── api/           # API endpoints and routing
│   ├── config/        # Configuration and settings
│   ├── core/          # Core business logic
│   └── database/      # Database models and setup
├── tests/             # Test files
├── .env              # Environment variables
├── requirements.txt   # Python dependencies
└── run.py            # Application entry point
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_agent_manager.py

# Run with coverage
pytest --cov=src tests/
```

## 🔒 Security

- All endpoints require authentication (TODO)
- API keys are managed via environment variables
- Database connections are properly managed
- Input validation on all endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ✨ Future Enhancements

- [ ] Add authentication and authorization
- [ ] Implement rate limiting
- [ ] Add more agent tools and capabilities
- [ ] Enhance monitoring and analytics
- [ ] Add support for multiple LLM providers
- [ ] Implement agent collaboration features

## 🐛 Known Issues

- Currently only supports single-user mode
- Limited to OpenAI's API
- Basic error handling

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

Made with ❤️ by [Your Name]