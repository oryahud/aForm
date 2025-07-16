# aForm

A modern, collaborative form builder application with comprehensive question types, Google OAuth authentication, and real-time collaboration features. Built with Flask, MongoDB, and modern web technologies.

## ✨ Quick Start

```bash
# Clone and install
git clone <repository-url>
cd aForm
pip install -r requirements.txt

# Set up environment variables (see Installation section)
cp .env.example .env

# Start MongoDB and run the app
python main.py
```

Visit `http://localhost:5000` and start building forms!

## Features

### 🔐 Authentication & Security
- Google OAuth2 integration for secure login
- Role-based access control (Admin, User)
- Form-level permissions (Admin, Editor, Viewer)
- Session management with secure secrets

### 📝 Form Builder
- Intuitive form creation interface with modern design
- **13 comprehensive question types** with full validation:
  - 📝 **Text Input** - Single-line text with custom placeholders
  - 📧 **Email Address** - Email validation with HTML5 support
  - 📱 **Phone Number** - International format with country codes and extensions
  - 📅 **Date Picker** - Date selection with min/max constraints
  - 🕐 **Time Picker** - Time selection with 24-hour format
  - 🔗 **Website URL** - URL validation with protocol checking
  - 🔢 **Number Input** - Numeric input with range validation and step controls
  - ⭐ **Rating Scale** - Interactive star ratings, sliders, or dropdown scales
  - 🔘 **Multiple Choice** - Single-select radio buttons with custom options
  - ☑️ **Checkboxes** - Multi-select checkboxes for multiple answers
  - 📋 **Dropdown** - Select menus with single or multiple selection
  - 📄 **Long Text** - Multi-line textarea with character limits and counters
  - 📎 **File Upload** - File attachments with type restrictions and size limits
- Real-time form preview with interactive elements
- Auto-save functionality with unsaved changes detection
- Modern, responsive UI design with SaaS-style components

### 👥 Collaboration
- Invite users via email to collaborate on forms
- Role-based permissions per form:
  - **Admin**: Full control (edit, publish, manage collaborators, delete)
  - **Editor**: Edit form questions and view submissions
  - **Viewer**: View submissions only
- Email invitations with personalized messages
- Collaborator management interface

### ⚙️ Advanced Question Features
- **Phone Numbers**: Country code selection, extension support, format validation
- **Date/Time**: Min/max date constraints, custom date formats, time validation
- **Rating Systems**: Star ratings (1-10 scale), slider controls, dropdown ratings
- **File Uploads**: Multiple file types (PDF, DOC, images), size limits, type restrictions
- **Text Areas**: Character limits with real-time counters, custom row heights
- **Number Inputs**: Min/max values, step controls, decimal support
- **Validation**: Client-side and server-side validation for all question types
- **Accessibility**: Full keyboard navigation, screen reader support, ARIA labels

### 📊 Form Management
- Public form sharing with unique URLs
- Form status management (draft/published)  
- Submission tracking and viewing with support for all question types
- Form deletion with proper permissions
- Bulk operations and filtering
- Export submissions in various formats

### 📧 Email Integration
- Automated invitation emails via Flask-Mail
- SMTP configuration support
- Email template customization
- Fallback for development environments

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd aForm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=aform

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

4. Set up MongoDB:
   - Install MongoDB locally or use MongoDB Atlas (cloud)
   - For local installation: [MongoDB Installation Guide](https://docs.mongodb.com/manual/installation/)
   - For MongoDB Atlas: [MongoDB Atlas Setup](https://docs.atlas.mongodb.com/getting-started/)
   - Start MongoDB service (local): `mongod`
   - Create database: `aform` (will be created automatically on first use)

5. Set up Google OAuth:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable Google+ API
   - Create OAuth 2.0 credentials
   - Add authorized redirect URIs: `http://localhost:5000/auth/callback`

## Usage

Start the application:
```bash
python main.py
```

The application will be available at `http://localhost:5000`

## Project Structure

```
aForm/
├── app.py                    # Main Flask application
├── auth.py                  # Authentication and authorization logic
├── database.py              # MongoDB connection and configuration
├── models.py                # Database models with serialization
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── requirements-ci.txt      # CI/CD dependencies (MongoDB-free)
├── static/                 # Static assets
│   ├── css/               # Modern SaaS-style CSS
│   │   ├── modern-saas.css
│   │   └── public_form.css
│   └── js/                # Enhanced JavaScript
│       ├── form_builder.js
│       └── public_form.js
├── templates/             # HTML templates
│   ├── form_builder_modern.html
│   ├── my_forms_modern.html
│   ├── public_form_modern.html
│   └── ...
├── tests/                 # Comprehensive test suite
│   ├── test_question_types.py
│   ├── test_forms.py
│   ├── test_public_forms.py
│   └── conftest.py
└── .github/               # GitHub Actions CI/CD
    └── workflows/
        └── tests.yml
```

## API Endpoints

### Authentication
- `GET /login` - Login page
- `GET /auth/google` - Google OAuth login
- `GET /auth/callback` - OAuth callback
- `POST /logout` - Logout

### Forms
- `GET /` - Dashboard (my forms)
- `POST /create-form` - Create new form
- `GET /form/<name>/edit` - Form builder
- `POST /api/form/<name>/save` - Save form data
- `POST /api/form/<name>/publish` - Publish form
- `DELETE /api/form/<name>` - Delete form

### Collaboration
- `POST /api/form/<name>/invite` - Invite collaborator
- `GET /api/form/<name>/collaborators` - List collaborators
- `DELETE /api/form/<name>/collaborators/<user_id>` - Remove collaborator

### Public Forms
- `GET /submit/<name>` - Public form view with all question types
- `POST /api/form/<name>/submit` - Submit form response with validation
- `GET /form/<name>/submissions` - View submissions with all data types

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: MongoDB with PyMongo
- **Authentication**: Google OAuth2 via Authlib
- **Email**: Flask-Mail
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Icons**: Feather Icons
- **Storage**: MongoDB (production-ready)

## Testing

The application includes comprehensive test coverage for all features:

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_question_types.py -v
python -m pytest tests/test_forms.py -v

# Run with coverage
python -m pytest --cov=. --cov-report=html
```

### Test Coverage

- **Question Types**: Complete validation testing for all 13 question types
- **Form Management**: CRUD operations, permissions, collaboration
- **Authentication**: Google OAuth flow, session management
- **Public Forms**: Form rendering, submission handling, data validation
- **Email Integration**: Invitation emails, SMTP configuration
- **Database**: MongoDB operations, data serialization

## Development

The application uses MongoDB for data storage, making it production-ready and scalable. For local development, ensure MongoDB is running on your system.

### Running in Development Mode

```bash
python main.py
```

The app runs with `debug=True` by default, enabling hot reload and detailed error messages.

### Development Features

- **Hot Reload**: Automatic server restart on code changes
- **Error Handling**: Detailed error messages with stack traces
- **MongoDB Integration**: Full database operations with proper serialization
- **Session Management**: Secure session handling with Google OAuth
- **CI/CD**: GitHub Actions workflow for automated testing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.