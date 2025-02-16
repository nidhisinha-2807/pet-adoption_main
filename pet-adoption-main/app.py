import subprocess
from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# Connect to MySQL database
db = mysql.connector.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', 'root'),
    database=os.environ.get('DB_NAME', 'pet_adoption_db')
)
cursor = db.cursor()

# Define database setup function
def setup_database():
    # Execute schema.sql to create tables if they don't exist
    subprocess.call(['mysql', '-u', os.environ.get('DB_USER', 'root'), '-p' + os.environ.get('DB_PASSWORD', 'root'), os.environ.get('DB_NAME', 'pet_adoption_db'), '-e', 'source sql/schema.sql'])

    # Check if pets table is empty
    cursor.execute("SELECT COUNT(*) FROM pets")
    result = cursor.fetchone()
    if result[0] == 0:
        # Execute data.sql to populate tables with sample data if the table is empty
        subprocess.call(['mysql', '-u', os.environ.get('DB_USER', 'root'), '-p' + os.environ.get('DB_PASSWORD', 'root'), os.environ.get('DB_NAME', 'pet_adoption_db'), '-e', 'source sql/data.sql'])
    else:
        print("Table 'pets' already has data.")

# Call setup_database function before each request
@app.before_request
def before_request_func():
    setup_database()


# Define routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_term = request.form['search']
        cursor.execute("SELECT * FROM pets WHERE name LIKE %s OR species LIKE %s", ('%' + search_term + '%', '%' + search_term + '%'))
        pets = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM pets")
        pets = cursor.fetchall()
        # Fetch column names
        column_names = [desc[0] for desc in cursor.description]
        # Convert each row to a dictionary
        pets = [dict(zip(column_names, pet)) for pet in pets]
    
    print(pets)  # Print fetched pets
    
    return render_template('index.html', pets=pets)



@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        available = 1 if 'available' in request.form else 0
        
        # Insert new pet into the database
        cursor.execute("INSERT INTO pets (name, species, age, available) VALUES (%s, %s, %s, %s)", (name, species, age, available))
        db.commit()

        return redirect(url_for('index'))
    
    return render_template('add_pet.html')

@app.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        available = 1 if 'available' in request.form else 0
        
        # Update pet details in the database
        cursor.execute("UPDATE pets SET name=%s, species=%s, age=%s, available=%s WHERE id=%s", (name, species, age, available, pet_id))
        db.commit()

        return redirect(url_for('index'))
    
    cursor.execute("SELECT * FROM pets WHERE id = %s", (pet_id,))
    pet = cursor.fetchone()
    return render_template('edit_pet.html', pet=pet)

@app.route('/delete_pet/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    cursor.execute("DELETE FROM pets WHERE id = %s", (pet_id,))
    db.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)