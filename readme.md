🚂 Railway Ticket Booking System (Modular Edition)A high-performance, secure, and modular web application for booking train tickets. Originally a monolith, this project has been re-architected into a scalable Flask Blueprint structure with MongoDB Atlas integration.🚀 Key FeaturesModular Architecture: Refactored into a clean railway_app package with dedicated Blueprints for Auth, Booking, Main, and Admin.MongoDB Atlas Optimized:High-Speed Search: Database-level range filtering and Compound Indexes ensure instant search results.Aggregation Pipeline: Solves the "N+1 Query" problem by calculating seat availability in a single database trip (replacing legacy MapReduce).Security First:CSRF Protection: All forms secured globally with Flask-WTF.Secure Auth: Password hashing with Werkzeug and session management.Environment Config: Credentials managed via .env or Vercel Environment Variables.Advanced Ticketing:Smart Allocation: Auto-assigns Confirmed, RAC, or Waitlist status.PDF Generation: Generates professional tickets with Blue Header styling and dynamic QR Codes.Email Integration: Sends booking confirmations via SMTP.Admin Dashboard: comprehensive panel to manage trains and view bookings with real-time client-side search.🛠️ Tech Stack & ArchitectureBackend: Python 3.11+, Flask (Blueprints, Application Factory)Database: MongoDB (via MongoEngine ODM)Frontend: Jinja2 Templates, Bootstrap 5Utilities: fpdf (PDFs), qrcode (QR Gen), flask-mail (Email)Deployment: Vercel (Serverless Function compatible)Folder Structure/railway-booking-system
│
├── app.py              # Application Entry Point (Launcher)
├── config.py           # Configuration Class
├── models.py           # Database Schemas & Indexes
├── vercel.json         # Vercel Deployment Config
├── requirements.txt    # Dependencies
│
└── railway_app/        # Main Package
    ├── __init__.py     # App Factory & Extensions (CSRF, Mail, DB)
    ├── utils.py        # Helper Functions (PDF, Email, Logic)
    │
    ├── routes/         # Modular Logic
    │   ├── auth.py     # Login/Signup
    │   ├── booking.py  # Ticket Booking & PNR
    │   ├── main.py     # Search & Homepage
    │   └── admin.py    # Dashboard
    │
    ├── templates/      # Jinja2 HTML Files
    └── static/         # CSS & Assets
⚙️ Setup & Installation1. PrerequisitesPython 3.10+ installed.MongoDB Atlas Account (or local MongoDB).Gmail Account (for sending ticket emails).2. InstallationClone the repository:git clone [https://github.com/yourusername/railway-booking-system.git](https://github.com/yourusername/railway-booking-system.git)
cd railway-booking-system
Create a Virtual Environment:python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
Install Dependencies:pip install -r requirements.txt
Configure Environment:Create a .env file in the root directory:SECRET_KEY=your_super_secret_key_here
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/railway_db
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
3. Initialize DatabaseRun the initialization script to seed the database with sample trains and users:python init_db.py
4. Run the Applicationpython app.py
Visit http://127.0.0.1:5000 in your browser.☁️ Deployment (Vercel)This project is configured for seamless deployment on Vercel.Prepare: Ensure vercel.json exists in the root and app.py uses the create_app() pattern.Push to GitHub: Commit all your changes.Import to Vercel: Connect your repository.Environment Variables: In Vercel Project Settings, add:MONGO_URISECRET_KEYEMAIL_USEREMAIL_PASSDeploy: Vercel will auto-detect the Python app and launch it.🛡️ Security NotesCSRF Tokens: Every form submission requires a {{ csrf_token() }}. If you see a "400 Bad Request," check if the form has the hidden token input.Production: Ensure DEBUG is set to False in production environments.🤝 ContributingFork the repo.Create a feature branch (git checkout -b feature/NewFeature).Commit your changes.Push to the branch and open a Pull Request.Disclaimer: This is a portfolio project demonstrating Flask architecture patterns. Do not use real