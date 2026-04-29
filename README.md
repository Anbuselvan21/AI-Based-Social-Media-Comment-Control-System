# AI-Based Social Media Comment Control System

## Project Overview
This is a full-stack web application for moderating social media comments using AI models.

## Folder Structure

```
comment-control/
├── backend/
│   ├── app.py                  # Main Flask application
│   ├── models/
│   │   ├── __init__.py
│   │   ├── text_model.py        # Text classification model
│   │   └── image_model.py       # Image classification model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   ├── predict.py          # Prediction routes
│   │   └── admin.py            # Admin routes
│   ├── database.py             # Database configuration
│   ├── requirements.txt
│   └── models/                  # Trained model files
│       ├── comment_moderation_model.pth
│       ├── hate_speech_model.pth
│       └── final_multimodal_model.pth
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── Dashboard.js
│   │   │   ├── TextComment.js
│   │   │   ├── ImageComment.js
│   │   │   ├── AdminPanel.js
│   │   │   └── Navbar.js
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   ├── package.json
│   └── .env
│
├── README.md
└── SETUP.md
```

## Tech Stack

- **Frontend**: React.js, React Router, Axios
- **Backend**: Flask, Flask-CORS, Flask-JWT-Extended
- **Database**: SQLite (for simplicity, can be replaced with PostgreSQL)
- **AI Models**: PyTorch (DistilBERT/CNN)

## Features

1. User Authentication (Login/Register)
2. Text Comment Analysis with real-time feedback
3. Image Comment Analysis
4. Admin Dashboard with analytics
5. Comment history and management
