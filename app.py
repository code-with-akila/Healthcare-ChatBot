from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import re
from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote_plus
import certifi

app = Flask(__name__)

# MongoDB Atlas Connection
username_mongo = quote_plus("akila_12345")
password_mongo = quote_plus("Akila@2004")
mongo_uri = f"mongodb+srv://{username_mongo}:{password_mongo}@cluster0.icdphl8.mongodb.net/"
client = MongoClient("mongodb+srv://akila_12345:Akila@2004@cluster0.icdphl8.mongodb.net/healthcare_chatbot?retryWrites=true&w=majority",tls = True,
tlsCAFile=certifi.where())
db = client.healthcare_chatbot # Choose a database name
users_collection = db.users
feedback_collection = db.feedback

# Configure the API key
genai.configure(api_key="AIzaSyD4A9VjzenlfqayTpxIcF_d9-HRUxvpKUc")

# Define generation configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

# Create the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

# Set the system instructions for healthcare
model.system_instruction = (
    "You are a healthcare assistant chatbot. Your role is to provide general health information, "
    "symptom checking, and basic medical advice. Always remind users that you are not a replacement "
    "for professional medical advice. Collect the following information from users:\n"
    "1. Age\n"
    "2. Gender\n"
    "3. Main symptoms or concerns\n"
    "4. Any existing medical conditions\n"
    "5. Current medications (if any)\n\n"
    "Provide clear, accurate, and helpful responses while maintaining medical ethics. "
    "If the situation seems serious, always recommend consulting a healthcare professional. "
    "Never make definitive diagnoses or prescribe medications."
)

def format_response(text):
    # Replace markdown-style bold text with HTML bold tags
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Replace markdown-style list items with HTML list items
    text = re.sub(r'\* (.*?)\n', r'<li>\1</li>', text)
    
    # Wrap list items with <ul> tags
    text = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    
    # Convert newlines to <br> for single line breaks
    text = text.replace('\n', '<br>')

    return text

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users_collection.find_one({'username': username, 'password': password}) # In real app, hash password
        if user:
            return render_template('chat.html') # Redirect to chat page on successful login
        else:
            return render_template('login.html', error="Invalid username or password") # Show error on login page
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if username already exists
        if users_collection.find_one({'username': username}):
            return render_template('register.html', error="Username already exists!")
        
        users_collection.insert_one({'username': username, 'password': password}) # In real app, hash password
        return render_template('login.html', success="Registration successful! Please login.")
    return render_template('register.html')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        feedback_collection.insert_one({
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'timestamp': datetime.now()
        })
        
        print(f"Feedback Received:\nName: {name}\nEmail: {email}\nSubject: {subject}\nMessage: {message}")
        return render_template('contact.html', success_message="Thank you for your feedback!")
    return render_template('contact.html')

@app.route('/logout')
def logout():
    # In a real application, you would clear the user's session here
    # For now, we'll just render the logout page
    return render_template('logout.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    
    response = model.generate_content(user_input)
    formatted_response = format_response(response.text)
    
    return jsonify({
        'response': formatted_response,
        'speech_text': response.text # Always send the response text for speech
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
