### 🚂 Railway Ticket Booking System
  This is a Python-based web application built with the Flask framework for a railway ticket booking system. It features a robust backend, a flexible database schema, and a modern, responsive user interface.

### ✨ Features
### User & Admin Management
User Authentication: Secure user registration, login, and logout. Passwords are hashed using werkzeug.security.

Admin Dashboard: A dedicated panel for administrators to manage all bookings and add new trains to the system.

Personalized Profile: Logged-in users can view and update their profile information. They can also save passenger details for faster bookings.

### Core Booking Functionality
Train Search: Users can search for trains by source and destination, with optional filters for different times of the day (morning, afternoon, evening).

Dynamic Booking System: The system handles seat allocation based on availability, assigning statuses like Confirmed, RAC (Reservation Against Cancellation), or Waitlisted.

PNR Status Check: Users can check the status of a ticket using a unique PNR number.

### Journey & Travel Planning
Detailed Train Routes: A dedicated page displays the full route of a train, including all stops and their arrival times.

Return Journey Suggestion: The system can intelligently suggest and direct the user to a return journey train based on their original booking.

### Ticket Generation & Output
Printable E-Ticket: A clean, printer-friendly HTML version of the ticket is available.

PDF Download: A professional-looking PDF e-ticket with a QR code containing key ticket details can be downloaded.

QR Code Integration: Each ticket includes a unique QR code that, when scanned, provides the PNR, passenger name, and status.

### 🗃️ Database Schema
The application uses an SQLite database with the following models:

User: Stores user credentials and profile information.

Train: Contains details about each train, including its route, departure, arrival, and total seats.

Route: A child model of Train that stores individual stops along a train's journey.

Booking: Records all ticket bookings, including passenger details, fare, and status.

Passenger: Allows users to save frequently traveling passengers for quick bookings.

### 🚀 Setup & Installation
Follow these steps to get the project up and running on your local machine.

### 1. Clone the repository
git clone https://github.com/rishabh0510rishabh/railway-booking-system
cd ticket-booking-app

### 2. Set up the Python environment
It is recommended to use a virtual environment.

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

### 3. Install required libraries
Install all the necessary dependencies from the requirements.txt file.

pip install -r requirements.txt

### 4. Initialize the database with a large dataset
The provided init_db.py script is designed to create a large-scale test environment. It will delete any existing railway.db file and populate a new one with ~200 trains and thousands of bookings to simulate real-world scenarios.

python init_db.py

### 5. Run the application
Start the Flask development server.

python app.py

The application will be available at http://127.0.0.1:5000. You can log in with the default admin account: username admin and password password123, or the test user username testuser and password password.