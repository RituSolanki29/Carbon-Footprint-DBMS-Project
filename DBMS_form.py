from flask import Flask,jsonify,render_template, request
import mysql.connector
import io
import base64
import matplotlib.pyplot as plt
import traceback 

app = Flask(__name__)

# Configure MySQL connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "manasaiscool",
    "database": "carbon_footprint"
}

@app.route('/home')
def home():
    return render_template('DBMS_Home.html')

@app.route('/dbms')
def dbms_page():
    return render_template('DBMS_Form.html')

@app.route('/trend_analysis')
def render_trend_analysis():
    return render_template('trend_analysis.html')

@app.route('/pie_chart')
def pie_chart():
    return render_template('pie_chart.html')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # Print form data for debugging
            print("Form Data:", request.form)

            is_veg = True if request.form["vegetarian"].lower() == "yes" else False
            meals = int(request.form["meals"]) if request.form["meals"] else 0
            transport_mode = request.form["transport"]
            duration = int(request.form["duration"]) if request.form["duration"] else 0
            flights_freq = request.form["frequency"]
            electricity_consumed = int(request.form["electricity"]) if request.form["electricity"] else 0
            waste_type = request.form["waste_type"]
            waste_quantity = int(request.form["waste_quantity"]) if request.form["waste_quantity"] else 0
            waste_freq = request.form["waste_frequency"]

            # Debugging: print assigned values
            print("Assigned Values: ", is_veg, meals, transport_mode, duration, flights_freq, electricity_consumed, waste_type, waste_quantity, waste_freq)

            # Handle edge cases for invalid or missing data
            if flights_freq == 'none':
                flights_freq = 'monthly'  # or set to default if none
            if not electricity_consumed:
                electricity_consumed = 0  # Set to 0 or handle as needed

            # Calculate footprint values
            food_footprint = calculate_food_footprint(is_veg, meals)
            travel_footprint = calculate_travel_footprint(transport_mode, duration, flights_freq)
            electricity_footprint = calculate_electricity_footprint(electricity_consumed)
            waste_footprint = calculate_waste_footprint(waste_quantity, waste_type, waste_freq)

            total_footprint = food_footprint + travel_footprint + electricity_footprint + waste_footprint

            suggestions = []
            if food_footprint > 4:
                suggestions.append("Consider reducing meat consumption to lower your food footprint.")
                suggestions.append("Swap red meat for plant-based options or lean meats like chicken.")
               
            if travel_footprint > 20:
                suggestions.append("Opt for public transportation or carpooling to reduce travel emissions.")
                suggestions.append("Walk, bike, or use public transportation instead of driving.")
               
            if electricity_footprint > 10:
                suggestions.append("Switch to energy-efficient appliances or reduce electricity usage.")
                suggestions.append("Unplug devices when not in use and reduce phantom power.")
                
            if waste_footprint > 4:
               suggestions.append("Recycle more and reduce waste generation to minimize your waste footprint.")
               suggestions.append("Avoid single-use plastics and choose reusable alternatives.")
              
        
            suggestions.append("Every small step counts—you're making a difference for the planet! 🌱")

            # Connect to MySQL and handle potential database errors
            try:
                connection = mysql.connector.connect(**db_config)
                if connection.is_connected():
                    print("Database connected successfully.")
                else:
                    raise Exception("Failed to connect to the database.")
            except mysql.connector.Error as err:
                print(f"Database connection error: {err}")
                return render_template("DBMS_1.html", error="Failed to connect to the database.")
            
            cursor = connection.cursor()

            query = """
                INSERT INTO user_data (
                    vegetarian, meals, transport, duration, flight_frequency,
                    electricity, waste_type, waste_quantity, waste_frequency,
                    food_footprint, travel_footprint, electricity_footprint,
                    waste_footprint, total_footprint
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = (
                "Yes" if is_veg else "No", meals, transport_mode, duration, flights_freq,
                electricity_consumed, waste_type, waste_quantity, waste_freq,
                food_footprint, travel_footprint, electricity_footprint,
                waste_footprint, total_footprint
            )
            cursor.execute(query, data)

            query_avg = """
                SELECT 
                    AVG(food_footprint), 
                    AVG(travel_footprint), 
                    AVG(electricity_footprint), 
                    AVG(waste_footprint) 
                FROM user_data
            """
            cursor.execute(query_avg)
            averages = cursor.fetchone()

            # Unpack averages
            avg_food, avg_travel, avg_electricity, avg_waste = averages

            connection.commit()

            # Close database resources
            cursor.close()
            connection.close()

            # Print output for debugging
            print(f"Total: {total_footprint}, Food: {food_footprint}, Travel: {travel_footprint}, Electricity: {electricity_footprint}, Waste: {waste_footprint}")
            print(f"Suggestions: {suggestions}")

            # Return results to the user
            return render_template("DBMS_result.html", 
                                    total=total_footprint,
                                    food=food_footprint, 
                                    travel=travel_footprint,
                                    electricity=electricity_footprint,
                                    waste=waste_footprint,
                                    suggestions=suggestions, 
                                    avg_food=avg_food, 
                                    avg_travel=avg_travel,
                                    avg_electricity=avg_electricity,
                                    avg_waste=avg_waste)

        except (ValueError, KeyError) as e:
            print(f"Error occurred: {e}")
            traceback.print_exc()  # Print full stack trace for detailed debugging
            return render_template("DBMS_Form.html", error="Please fill out all fields correctly.")
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            traceback.print_exc()
            return render_template("DBMS_Form.html", error="An unexpected error occurred.")

    return render_template("DBMS_Home.html")

def calculate_food_footprint(is_veg, frequency):
    if is_veg:
        footprint = frequency * 0.4
    else:
        footprint = frequency * 1.5
    return round(footprint, 2)

def calculate_travel_footprint(transport_mode, duration, flights_freq):
    if transport_mode == 'public':
        travel_footprint = duration * 0.2
    elif transport_mode == 'personal':
        travel_footprint = duration * 0.5
    elif transport_mode == 'flights': 
        if flights_freq == 'daily':
            travel_footprint = 10.0
        elif flights_freq == 'weekly':
            travel_footprint = 5.0
        elif flights_freq == 'monthly':
            travel_footprint = 2.0
        else:  # Handle cases where flights frequency is 'none' or invalid
            travel_footprint = 0
    else:  
        travel_footprint = 1.0
    return round(travel_footprint, 2)

def calculate_electricity_footprint(electricity_consumed):
    e = electricity_consumed * 0.5
    return round(e, 2)

def calculate_waste_footprint(waste_quantity, waste_type, disposal_freq):
    if waste_type == 'biodegradable':
        waste_footprint = waste_quantity * 0.2
    elif waste_type == 'non-biodegradable':
        waste_footprint = waste_quantity * 0.7
    else:
        waste_footprint = waste_quantity * 0.5

    if disposal_freq == 'daily':
        waste_footprint *= 1.0
    elif disposal_freq == 'weekly':
        waste_footprint *= 0.5
    elif disposal_freq == 'bi-weekly':
        waste_footprint *= 0.25
    else:
        waste_footprint *= 0.1

    return round(waste_footprint, 2)

@app.route('/get_pie_chart_data', methods=['GET'])
def get_pie_chart_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = """
            SELECT 
                AVG(food_footprint), 
                AVG(travel_footprint), 
                AVG(electricity_footprint), 
                AVG(waste_footprint) 
            FROM user_data
        """
        cursor.execute(query)
        averages = cursor.fetchone()

        data = {
            "labels": ["Food", "Travel", "Electricity", "Waste"],
            "values": [round(averages[0], 2), round(averages[1], 2), round(averages[2], 2), round(averages[3], 2)]
        }

        return jsonify(data)

    except Exception as e:
        return f"Error: {str(e)}", 503
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/average_data', methods=['GET'])
def average_data():
    try:
        connection = mysql.connector.connect(**db_config)  # Use db_config for connection
        cursor = connection.cursor()
        
        # Replace 'your_table_name' with the actual table name where footprint data is stored
        cursor.execute("""
            SELECT 
                AVG(food_footprint), 
                AVG(travel_footprint), 
                AVG(electricity_footprint), 
                AVG(waste_footprint) 
            FROM user_data  # Replace with your actual table name if different
        """)
        
        # Fetch the averages from the query result
        avg_food, avg_travel, avg_electricity, avg_waste = cursor.fetchone()
        
        avg_food = round(avg_food, 2)
        avg_travel = round(avg_travel, 2)
        avg_electricity = round(avg_electricity, 2)
        avg_waste = round(avg_waste, 2)

        # Return the averages in JSON format
        return jsonify({
            "avg_food": avg_food,
            "avg_travel": avg_travel,
            "avg_electricity": avg_electricity,
            "avg_waste": avg_waste
        })
    except Exception as e:
        # Return an error message if an exception occurs
        return f"Error: {str(e)}", 503
    finally:
        # Ensure the connection is closed after the operation
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/getemissiongraph', methods=['GET'])
def getemissiongraph():
    try:
        connection = mysql.connector.connect(**db_config)  # Use db_config for connection
        cursor = connection.cursor()
        query = """
            SELECT 
                id, 
                total_footprint AS total
            FROM 
                user_data
            GROUP BY 
                id
            ORDER BY 
                id;
            
        """
        cursor.execute(query)
        results = cursor.fetchall()  
        ids = [row[0] for row in results]   
        total = [row[1] for row in results] 
        return jsonify({"ids": ids, "total": total})
    
    except Exception as e:
        return f"Error: {str(e)}", 503
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/donut_chart')
def donut_chart():
    return render_template('donut_chart.html')

@app.route('/get_chart_data', methods=['GET'])
def get_chart_data():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = """
            SELECT 
                AVG(food_footprint), 
                AVG(travel_footprint), 
                AVG(electricity_footprint), 
                AVG(waste_footprint) 
            FROM user_data
        """
        cursor.execute(query)
        averages = cursor.fetchone()

        data = {
            "labels": ["Food", "Travel", "Electricity", "Waste"],
            "values": [round(averages[0], 2), round(averages[1], 2), round(averages[2], 2), round(averages[3], 2)]
        }

        return jsonify(data)

    except Exception as e:
        return f"Error: {str(e)}", 503
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


       

if __name__ == "__main__":
    app.run(debug=True)
