<img width="2914" height="1486" alt="image" src="https://github.com/user-attachments/assets/4494bd64-0c60-425a-b18c-f95b9d5b9472" />
<img width="2899" height="1493" alt="image" src="https://github.com/user-attachments/assets/bc84ab38-5302-4c4e-8208-1d073b518b45" />

![Poker Table](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GitHub stars](https://img.shields.io/github/stars/EMMA019/AI_pokergame?style=social)
![GitHub forks](https://img.shields.io/github/forks/EMMA019/AI_pokergame?style=social)
![GitHub issues](https://img.shields.io/github/issues/EMMA019/AI_pokergame)
![License](https://img.shields.io/github/license/EMMA019/AI_pokergame)

🃏 Midnight Luxury Poker
> A sophisticated online Texas Hold'em game where a challenging AI serves as your opponent, providing a realistic, real-time poker experience.
> 
🌟 Project Overview
"Midnight Luxury Poker" is a web application designed to let players enjoy Texas Hold'em against a dedicated AI opponent. The system is built on a robust Flask backend, utilizing Flask-SocketIO for real-time communication, and a clean, rich frontend built with standard web technologies. It offers a smooth, real-time gaming experience focused on strategic play against an intelligent AI.
🚀 Features
 * 💻 Full-Stack Architecture: Powered by Flask on the backend, with persistence handled by SQLAlchemy, and a responsive frontend using HTML/CSS/JavaScript.
 * 📡 Real-Time Gameplay: Leverages Flask-SocketIO for instant, event-driven game state synchronization.
 * 🤖 AI Opponent: Contains sophisticated poker logic within backend/app/poker/ai.py to provide a challenging strategic experience.
 * ⚖️ MIT Licensed: Free for use, modification, and distribution.
🛠️ Technology Stack
| Category | Component | Key Version |
|---|---|---|
| Web Framework | Flask | Flask==2.3.3 |
| Real-Time Comm. | Flask-SocketIO | Flask-SocketIO==5.3.6 |
| Database ORM | SQLAlchemy / Flask-SQLAlchemy | SQLAlchemy==2.0.25, Flask-SQLAlchemy==3.1.1 |
| WSGI Server | gunicorn / eventlet | gunicorn==21.2.0, eventlet==0.33.3 |
| Config/Tools | python-dotenv / Werkzeug | python-dotenv==1.0.1, Werkzeug==2.3.8 |
| Frontend | HTML5, CSS3, JavaScript |  |
⚙️ Setup and Running the Application
1. Clone the Repository
git clone https://github.com/EMMA019/AI_pokergame.git
cd AI_pokergame

2. Backend Setup
You will need a Python environment (Python 3.x recommended).
 * Create and Activate a Virtual Environment
   # Linux/macOS
python3 -m venv venv
source venv/bin/activate
# Windows
python -m venv venv
.\venv\Scripts\activate

 * Install Dependencies
   pip install -r backend/requirements.txt

 * Configure Environment Variables (.env) 📝
   Copy the sample file to create your local environment configuration file:
   cp backend/.env.sample backend/.env

   backend/.env.sample Content:
   This file specifies critical configuration for the Flask application and the database connection.
   # Flask Application Settings
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY="YOUR_RANDOM_SECRET_KEY_HERE"

# Database Configuration (Using SQLite for development)
# The development.sqlite file will be created in the project root.
SQLALCHEMY_DATABASE_URI=sqlite:///development.sqlite

# Real-time Communication Setup (Optional: for scaling)
# SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/0  

   Note: Ensure you replace "YOUR_RANDOM_SECRET_KEY_HERE" with a secure, random string in your .env file.
 * Run the Server
   Since the application uses SocketIO, it should be launched using an event-driven server like eventlet (as specified in requirements.txt).
   python backend/run.py

   The server should start on a local address, typically http://127.0.0.1:5000.
3. Access the Frontend
Once the server is running, open the main page in your web browser:
 * Access the URL provided by the running Flask server (e.g., http://127.0.0.1:5000).
📂 Project Structure
AI_pokergame/
├── backend/                  # Server-side (Flask/Python)
│   ├── app/
│   │   ├── poker/            # Core Poker Game Logic
│   │   │   ├── ai.py         # AI Strategy and Logic
│   │   │   ├── game.py       # Game State Management
│   │   │   └── routes.py     # Flask Blueprint/API Endpoints
│   ├── config.py             # Flask Configuration
│   ├── .env.sample           # Template for Environment Variables
│   └── requirements.txt      # Python Dependencies
├── frontend/                 # Client-side (Web)
│   ├── index.html            # Main Page Structure
│   ├── script.js             # Client-side Game Logic
│   └── style.css             # Styling
├── .gitignore                # Files/folders to ignore in Git
├── LICENCE                   # MIT License details
└── Readme.md                 # This file

📝 License
This project is released under the MIT License. See the LICENCE file for details.
