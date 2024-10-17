import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from sqlalchemy import text
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
CORS(app)

# Configurations using environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# Initialize extensions
mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Candidate model
class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="pending")
    year = db.Column(db.Integer, nullable=False)
    round = db.Column(db.String(50), nullable=False)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Email templates dictionary
email_templates = {
    "level1": [
        {
            "id": "level1_template1",
            "subject": "Level 1 Interview Task Assignment",
            "body": (
                "Dear {name},\n\n"
                "Congratulations on advancing to the Level 1 interview stage at Hash Agile Technologies! We are excited to have you progress further in our selection process.\n\n"
                "Please find below the instructions for your next task:\n\n"
                "### **Installation Instructions**\n\n"
                "1. **Read about Apache Solr:** Familiarize yourself with Solr by visiting the [Solr Tutorial](https://solr.apache.org/guide/).\n"
                "2. **Install Apache Solr:** Install Apache Solr on your local machine following the official [installation guide](https://solr.apache.org/guide/installing-solr.html).\n"
                "3. **Configure Solr Port:** Start the Solr service on port **8989** instead of the default port.\n"
                "4. **Download Employee Dataset:** Obtain the Employee Dataset from [Kaggle](https://www.kaggle.com/datasets/williamlucas0/employee-sample-data).\n\n"
                "Please complete the task and submit within 12 hours.\n\n"
                "Best regards,\n\nHash Agile Technologies"
            )
        }
        # Additional templates can be added here as needed
    ]
    # Add more levels and their templates here if required
}

@app.route('/')
def index():
    try:
        result = db.session.execute(text('SELECT 1')).scalar()
        return "Database connected successfully!"
    except Exception as e:
        return f"Database connection failed: {e}"

@app.route('/candidates', methods=['GET'])
def list_candidates():
    try:
        year = request.args.get('year')
        round_filter = request.args.get('round')
        
        query = Candidate.query
        if year:
            query = query.filter_by(year=year)
        if round_filter:
            query = query.filter_by(round=round_filter)

        candidates = query.all()
        result = [
            {
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "status": candidate.status,
                "year": candidate.year,
                "round": candidate.round
            }
            for candidate in candidates
        ]
        return jsonify({"candidates": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_candidate', methods=['POST'])
def add_candidate():
    try:
        data = request.get_json()
        new_candidate = Candidate(
            name=data['name'],
            email=data['email'],
            year=data['year'],
            round=data['round']
        )
        db.session.add(new_candidate)
        db.session.commit()
        return jsonify({"message": "Candidate added successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    try:
        candidate = Candidate.query.get(id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        data = request.get_json()
        new_status = data.get('status')

        if new_status not in ['selected', 'rejected']:
            return jsonify({"error": "Invalid status"}), 400

        candidate.status = new_status
        db.session.commit()
        
        send_status_email(candidate)
        return jsonify({"message": f"Candidate status updated to {new_status}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_status_email(candidate):
    if candidate.status == 'selected':
        subject = "Congratulations! You've been selected"
        body = f"Dear {candidate.name},\n\nWe are pleased to inform you that you have been selected for the position."
    else:
        subject = "Thank you for applying"
        body = f"Dear {candidate.name},\n\nWe regret to inform you that you have not been selected at this time."

    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[candidate.email])
    msg.body = body
    mail.send(msg)

@app.route('/get_templates', methods=['GET'])
def get_templates():
    try:
        round_filter = request.args.get('round')
        if not round_filter or round_filter not in email_templates:
            return jsonify({"error": "Invalid or missing round"}), 400

        templates = email_templates[round_filter]
        return jsonify({"templates": templates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/send_emails_by_filter', methods=['POST'])
def send_emails_by_filter():
    try:
        data = request.get_json()
        year = data.get('year')
        round_filter = data.get('round')
        status_filter = data.get('status')
        subject = data.get('subject')
        body = data.get('body')

        if not round_filter:
            return jsonify({"error": "Missing round"}), 400

        if not subject or not body:
            return jsonify({"error": "Subject and body are required"}), 400

        query = Candidate.query.filter_by(round=round_filter)
        if year:
            query = query.filter_by(year=year)
        if status_filter:
            query = query.filter_by(status=status_filter)

        candidates = query.all()
        if not candidates:
            return jsonify({"error": "No candidates found with the given filters"}), 404

        for candidate in candidates:
            formatted_subject = subject.format(name=candidate.name)
            formatted_body = body.format(name=candidate.name)
            msg = Message(formatted_subject, sender=app.config['MAIL_USERNAME'], recipients=[candidate.email])
            msg.body = formatted_body
            mail.send(msg)

        return jsonify({"message": f"Emails sent successfully to {len(candidates)} candidates!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete_candidate/<int:id>', methods=['DELETE'])
def delete_candidate(id):
    try:
        candidate = Candidate.query.get(id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404

        db.session.delete(candidate)
        db.session.commit()
        return jsonify({"message": "Candidate deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
