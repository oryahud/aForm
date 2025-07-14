# aForm

A modern, collaborative form builder application with Google OAuth authentication and real-time collaboration features.

## Features

### 🔐 Authentication & Security
- Google OAuth2 integration for secure login
- Role-based access control (Admin, User)
- Form-level permissions (Admin, Editor, Viewer)
- Session management with secure secrets

### 📝 Form Builder
- Drag-and-drop form creation interface
- Multiple question types (text, email, number, select, radio, checkbox, textarea)
- Real-time form preview
- Auto-save functionality with unsaved changes detection
- Modern, responsive UI design

### 👥 Collaboration
- Invite users via email to collaborate on forms
- Role-based permissions per form:
  - **Admin**: Full control (edit, publish, manage collaborators, delete)
  - **Editor**: Edit form questions and view submissions
  - **Viewer**: View submissions only
- Email invitations with personalized messages
- Collaborator management interface

### 📊 Form Management
- Public form sharing with unique URLs
- Form status management (draft/published)
- Submission tracking and viewing
- Form deletion with proper permissions
- Bulk operations and filtering

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

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

4. Set up Google OAuth:
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
├── app.py                 # Main Flask application
├── auth.py               # Authentication and authorization logic
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── forms.json           # Form data storage
├── users.json           # User data storage
├── static/              # Static assets
│   ├── css/            # Stylesheets
│   └── js/             # JavaScript files
└── templates/          # HTML templates
    ├── form_builder_modern.html
    ├── my_forms_modern.html
    ├── public_form_modern.html
    └── ...
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
- `GET /form/<name>` - Public form view
- `POST /form/<name>/submit` - Submit form response
- `GET /form/<name>/submissions` - View submissions

## Technologies Used

- **Backend**: Flask (Python)
- **Authentication**: Google OAuth2 via Authlib
- **Email**: Flask-Mail
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Icons**: Feather Icons
- **Storage**: JSON files (development)

## Development

The application uses JSON files for data storage, making it easy to set up for development. For production use, consider migrating to a proper database system.

### Running in Development Mode

```bash
python main.py
```

The app runs with `debug=True` by default, enabling hot reload and detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.