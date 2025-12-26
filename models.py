import random
import string
from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash  

db = MongoEngine()

class Route(db.EmbeddedDocument):
    stop_name = db.StringField(required=True)
    arrival_time = db.StringField(required=True)
    stop_order = db.IntField(required=True)

class Train(db.Document):
    train_name = db.StringField(required=True)
    source = db.StringField(required=True)
    destination = db.StringField(required=True)
    departure_time = db.StringField(required=True) 
    arrival_time = db.StringField()
    total_seats = db.IntField(required=True)
    route_stops = db.ListField(db.EmbeddedDocumentField(Route))

    @property
    def id(self):
        return str(self.pk)

class Passenger(db.EmbeddedDocument):
    name = db.StringField(required=True)
    age = db.IntField(required=True)
    berth_preference = db.StringField()
    uid = db.StringField(default=lambda: ''.join(random.choices(string.digits, k=8)))

class User(db.Document):
    username = db.StringField(unique=True, required=True)
    password_hash = db.StringField(required=True)
    role = db.StringField(default='user')
    email = db.StringField()
    phone_number = db.StringField()
    profile_picture = db.StringField()
    saved_passengers = db.ListField(db.EmbeddedDocumentField('Passenger'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    @property
    def id(self):
        return str(self.pk)

class Booking(db.Document):
    pnr_number = db.StringField(unique=True, required=True)
    train = db.ReferenceField(Train, required=True)
    user = db.ReferenceField(User, required=True)
    passenger_name = db.StringField(required=True)
    passenger_age = db.IntField(required=True)
    seat_class = db.StringField(default='Sleeper')
    berth_preference = db.StringField()
    status = db.StringField(default='Confirmed')
    seat_number = db.StringField()
    fare = db.FloatField(default=0.0)