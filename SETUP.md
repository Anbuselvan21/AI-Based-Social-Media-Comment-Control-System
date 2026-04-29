# AI-Based Social Media Comment Control System - Setup Guide

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn

## Project Structure

```
comment-control/
├── backend/                 # Flask Backend
│   ├── app.py              # Main application
│   ├── database.py         # Database configuration
│   ├── routes/             # API routes
│   │   ├── auth.py         # Authentication routes
│   │   ├── predict.py      # Prediction routes
│   │   └── admin.py        # Admin routes
│   ├── models/             # ML models
│   │   ├── text_model.py   # Text classifier
│   │   └── image_model.py  # Image classifier
│   ├── requirements.txt    # Python dependencies
│   └── uploads/            # Uploaded images
│
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.js          # Main app component
│   │   ├── App.css         # Styling
│   │   └── index.js        # Entry point
│   └── package.json        # Node dependencies
│
└── Model/                  # Trained models (from your folder)
    ├── comment_moderation_model.pth
    ├── hate_speech_model.pth
    └── final_multimodal_model.pth
```

## Backend Setup

### 1. Navigate to backend directory

```bash
cd comment-control/backend
```

### 2. Create virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Copy trained models

Copy your trained model files from the `Model` folder to `backend/`:
- `comment_moderation_model.pth`
- `hate_speech_model.pth`  
- `final_multimodal_model.pth`

### 5. Run the backend server

```bash
python app.py
```

The backend will run on `http://localhost:5000`

## Frontend Setup

### 1. Open a new terminal and navigate to frontend directory

```bash
cd comment-control/frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Default Admin Credentials

- **Username:** admin
- **Password:** admin123

## User Registration

Navigate to `http://localhost:3000/register` to create a new user account.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/admin/login` - Admin login
- `GET /api/auth/me` - Get current user

### Predictions
- `POST /api/predict-text` - Predict text comment
- `POST /api/predict-text/realtime` - Real-time text analysis
- `POST /api/predict-image` - Predict image comment
- `GET /api/history` - Get user's comment history

### Admin
- `GET /api/admin/dashboard` - Get dashboard stats
- `GET /api/admin/comments` - Get all comments (with filters)
- `DELETE /api/admin/comments/:id` - Delete comment
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users/:id/block` - Block/unblock user
- `DELETE /api/admin/users/:id/delete` - Delete user
- `GET /api/admin/export/csv` - Export comments as CSV

## Features

### User Features
1. **User Registration & Login** - Secure authentication
2. **Text Comment Analysis** - Real-time feedback with AI prediction
3. **Image Comment Analysis** - Upload and analyze images
4. **Comment History** - View past predictions
5. **Confidence Scores** - See prediction confidence percentages

### Admin Features
1. **Dashboard Analytics** - Overview statistics with charts
2. **Comment Management** - View, filter, and delete comments
3. **User Management** - Block/unblock users
4. **Export Reports** - Download CSV/PDF reports
5. **Real-time Monitoring** - Track content trends

### Prediction Categories
- **Non-Abusive** (Green) - Safe content
- **Intermediate** (Orange) - Borderline content
- **Abusive** (Red) - Offensive content

## Environment Variables

### Backend (.env)
```
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:5000/api
```

## Troubleshooting

### Port Already in Use
If port 5000 or 3000 is already in use, you can change them:
- Backend: Edit `app.py` and change `app.run(debug=True, port=5000)`
- Frontend: Edit `package.json` and change the PORT in scripts

### Model Loading Errors
If you encounter model loading errors:
1. Make sure the `.pth` files are in the correct location (`backend/`)
2. Check that PyTorch is properly installed
3. The system will fall back to simpler models if trained models fail to load

### Database Issues
The SQLite database will be automatically created on first run. If you need to reset:
```bash
rm backend/database.db
python backend/app.py  # This will recreate it
```

## Deployment

### Building for Production

**Frontend:**
```bash
npm run build
```
This creates an optimized build in `frontend/build/`

**Backend:**
For production, use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Technologies Used

### Backend
- Flask - Web framework
- Flask-JWT-Extended - JWT authentication
- PyTorch - Deep learning models
- Transformers - NLP models
- SQLite - Database

### Frontend
- React.js - UI framework
- React Router - Navigation
- Axios - HTTP client
- Recharts - Data visualization
- Lucide React - Icons

## Support

For issues or questions, please check:
1. The terminal/console for error messages
2. Network tab in browser dev tools for API errors
3. Backend logs for server-side errors

## License

This project is for educational purposes.
