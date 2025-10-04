# FastAPI Authentication Setup for Simple UI

This document explains how to set up the FastAPI backend to work with the simple_ui frontend, including Google Firebase authentication and email/password registration.

## Features Added

### 🔐 Authentication Systems
1. **Google Firebase Authentication**
   - Compatible with existing Firebase config from final_ui
   - Token verification through Firebase Admin SDK
   - User profile management

2. **Email/Password Authentication**
   - User registration with email validation
   - Secure password hashing using bcrypt
   - Simple token-based authentication

3. **User Form Management**
   - Persistent user preference storage
   - Automatic form data integration with story generation
   - Conditional form updates (only if not already filled)

### 📚 Enhanced Story Generation
- Stories are automatically personalized using saved user form data
- Fallback to request parameters when form data is not available
- Multi-language support (English/Hindi)
- Child-specific personalization (name, age, interests, etc.)

## Setup Instructions

### 1. Install Dependencies

Run the installation script:
```bash
cd backend_configured
python install_auth_deps.py
```

Or install manually:
```bash
pip install firebase-admin==6.5.0 email-validator==2.1.1 bcrypt==4.1.2
```

### 2. Firebase Configuration (Optional)

For Google authentication to work, you need to set up Firebase Admin SDK:

#### Option A: Using Service Account Key
1. Download your Firebase service account key JSON file
2. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

#### Option B: Using Default Credentials
If running on Google Cloud or with gcloud SDK configured, the app will use default credentials automatically.

#### Option C: Without Firebase
The app will work without Firebase - only email/password authentication will be available.

### 3. Start the Server

```bash
cd backend_configured
python fastapi_app.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register with email/password |
| `/auth/login` | POST | Login with email/password |
| `/auth/firebase` | POST | Authenticate with Firebase token |
| `/auth/me` | GET | Get current user profile |
| `/auth/logout` | POST | Logout (logging only) |

### User Form Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/user/form` | GET | Get user form data |
| `/user/form` | POST | Update user form data |
| `/user/form/check` | GET | Check if form needs filling |

### Story Generation (Enhanced)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate-story` | POST | Generate story (uses form data if available) |
| `/generate-story-personalized` | POST | Generate fully personalized story |

## Request/Response Examples

### Register User
```json
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe"
}
```

### Update User Form
```json
POST /user/form
{
  "form_data": {
    "child_name": "Emma",
    "child_age": 8,
    "child_gender": "she",
    "interests": ["dinosaurs", "space", "art"],
    "reading_level": "medium",
    "location": "New York",
    "mother_tongue": "Spanish",
    "language_preference": "english"
  }
}
```

### Generate Story (Auto-Enhanced)
```json
POST /generate-story
{
  "theme": "adventure",
  "age_group": "6-10",
  "story_length": "medium",
  "include_images": true
}
```

## Frontend Integration

### Simple UI Compatibility
- The FastAPI app serves the simple_ui frontend at the root URL (`/`)
- Static files are served from `/static/`
- All API endpoints are CORS-enabled for frontend integration

### Authentication Flow
1. User logs in via simple_ui (Google or email/password)
2. Frontend stores authentication token
3. Token is sent with API requests via Authorization header
4. Backend automatically enhances story generation with user preferences

### Form Management Flow
1. Check if user needs to fill form: `GET /user/form/check`
2. If needed, show form and submit: `POST /user/form`
3. Form data is automatically used in subsequent story generations

## Security Considerations

⚠️ **Important for Production:**

1. **CORS Configuration**: Update CORS origins in production to only include your domain
2. **Token Security**: Implement proper JWT tokens instead of simple tokens for email auth
3. **Database**: Replace in-memory storage with a proper database (PostgreSQL, MongoDB)
4. **Environment Variables**: Store sensitive config in environment variables
5. **HTTPS**: Use HTTPS in production
6. **Rate Limiting**: Add rate limiting for API endpoints

## Troubleshooting

### Firebase Issues
- If Firebase import fails, check that `firebase-admin` is installed
- Verify Firebase credentials are properly configured
- App will work without Firebase (email auth only)

### CORS Issues
- Check that your frontend URL is in the CORS allowed origins
- Ensure credentials are included in frontend requests

### Form Data Issues
- Form data persists only while the server is running (in-memory storage)
- For production, implement proper database storage

## Development Notes

- User data is stored in memory and will be lost on server restart
- Firebase authentication requires proper service account setup
- The app gracefully handles missing Firebase configuration
- All authentication is optional - the app works for anonymous users too