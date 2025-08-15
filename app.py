from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

# Initialize the Flask app
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///railway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with your Flask app
db = SQLAlchemy(app)


class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False) # e.g., '06:15'
    total_seats = db.Column(db.Integer, nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pnr_number = db.Column(db.String(20), unique=True, nullable=False)
    train_id = db.Column(db.Integer, db.ForeignKey('train.id'), nullable=False)
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Confirmed')
    
    train = db.relationship('Train', backref=db.backref('bookings', lazy=True))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']

    # Query the database for matching trains
    trains = Train.query.filter_by(source=source, destination=destination).all()

    # We will create results.html in the next step
    return render_template('results.html', trains=trains, source=source, destination=destination)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)