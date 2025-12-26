[Railway_Booking_System.md](https://github.com/user-attachments/files/24346396/Railway_Booking_System.md)
# 🚂 Railway Booking System

A robust, full-stack web application for searching, booking, and managing train tickets.  
Built with **Flask** and **MongoDB**, this project features a modular architecture, real-time seat availability calculation, and automated e-ticket generation.

---

## 🌟 Key Features

### 👤 User & Profile Management
- **Secure Authentication**: User registration and login with password hashing  
- **Profile Management**: Update personal details and manage saved passengers for faster bookings  
- **Booking History**: View past and upcoming journeys with status updates  

### 🚆 Train Search & Booking
- **Smart Search**: Filter trains by source, destination, and departure time (Morning, Afternoon, Evening)  
- **Real-time Availability**: Dynamic calculation of Confirmed, RAC, and Waitlisted seats using MongoDB aggregation pipelines  
- **Seat Allocation**: Automated logic for assigning seat numbers and berths based on class and preference  
- **Waitlist Logic**: Automatically handles Confirmed vs. RAC vs. Waitlist status based on capacity  

### 🎫 Ticketing System
- **PDF Generation**: Instantly download professional PDF tickets with unique PNRs  
- **QR Code Integration**: Embedded QR codes on tickets for easy validation  
- **Email Notifications**: Booking confirmations sent directly to the user's email via SMTP  
- **PNR Status**: Publicly accessible PNR status checker  

### 🛠 Admin Dashboard
- **Manage Trains**: Add new trains, routes, and schedules  
- **Booking Overview**: View all bookings across the system with search functionality  
- **Route Visualization**: View detailed route stops and timings  

---

## 💻 Tech Stack

**Backend**
- Python  
- Flask (Blueprints, Application Factory Pattern)

**Database**
- MongoDB (MongoEngine ODM)

**Frontend**
- Jinja2 Templates  
- Bootstrap 5  
- CSS3  

**Utilities**
- FPDF (PDF Generation)  
- QRCode (Ticket Validation)  
- Flask-Mail (Email Services)  
- Flask-WTF (Form Handling & CSRF Protection)  

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10+  
- MongoDB (Local or Atlas)  
- Gmail Account (for email notifications – App Password required)

### Steps

#### Clone the Repository
```bash
git clone https://github.com/yourusername/railway-booking-system.git
cd railway-booking-system
```

#### Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secure_secret_key
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/railway_db
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

#### Initialize Database
Run the script to populate the database with sample trains and users:
```bash
python init_db.py
```

#### Run the Application
```bash
python app.py
```
Visit: **http://127.0.0.1:5000**

---

## 📂 Project Structure

```
railway-booking-system/
├── app.py                  # Entry point
├── config.py               # App configuration
├── init_db.py              # Database seeder script
├── models.py               # Database schemas (User, Train, Booking)
├── requirements.txt        # Dependencies
└── railway_app/            # Main Application Package
    ├── __init__.py         # App factory & extension init
    ├── utils.py            # Helper functions (PDF, Email, Logic)
    ├── routes/             # Blueprints
    │   ├── admin.py
    │   ├── auth.py
    │   ├── booking.py
    │   └── main.py
    ├── static/             # CSS, Images
    └── templates/          # HTML Templates
```

---

## 🤝 Contributing

Contributions are welcome!  
Please follow these steps:

1. Fork the project  
2. Create your feature branch  
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. Commit your changes  
   ```bash
   git commit -m "Add some AmazingFeature"
   ```
4. Push to the branch  
   ```bash
   git push origin feature/AmazingFeature
   ```
5. Open a Pull Request  

---

## 📜 License

Distributed under the **MIT License**.  
See `LICENSE` for more information.
