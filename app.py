import serial
import time
from flask import Flask, render_template, request, jsonify
import threading
import glob
import busio
import board
import adafruit_ahtx0
import time
import sqlite3

app = Flask(__name__)

arduino = serial.Serial('/dev/ttyUSB0', 115200)  
time.sleep(2)  

BASE_DIR = '/sys/bus/w1/devices/'
DB_FILE = 'sensor_data.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            soil_moisture_1 FLOAT,
            soil_moisture_2 FLOAT,
            soil_temperature_1 FLOAT,
            soil_temperature_2 FLOAT,
            air_humidity_1 FLOAT,
            air_humidity_2 FLOAT,
            air_temperature_1 FLOAT,
            air_temperature_2 FLOAT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db():
    while True:
        def process_measurement(value):
            if value in [None, "N/A", "null"]: 
                return None  
            try:
                return round(float(value), 2)  
            except ValueError:
                return None  
        sm1 = process_measurement(soil_moisture1)
        sm2 = process_measurement(soil_moisture2)
        temp1 = process_measurement(temperature)
        temp2 = process_measurement(temperature2)
        hum1 = process_measurement(aht_hum1)
        hum2 = process_measurement(aht_hum2)
        t1 = process_measurement(aht_temp1)
        t2 = process_measurement(aht_temp2)        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO all_measurements (
                timestamp, soil_moisture_1, soil_moisture_2,
                soil_temperature_1, soil_temperature_2,
                air_humidity_1, air_humidity_2,
                air_temperature_1, air_temperature_2
            ) VALUES (?,?,?,?,?,?,?,?,?)
        ''', (
            time.strftime("%Y-%m-%d %H:%M:%S"),  
            sm1, sm2,                   
            temp1, temp2,               
            hum1, hum2,                
            t1, t2                      
        ))
        conn.commit()
        conn.close()
        time.sleep(15)

def initialize_aht20():
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_ahtx0.AHTx0(i2c)
        return sensor
    except Exception as e:
        print(f"Error initializing AHT20 sensor: {e}")
        return None

def read_aht20(sensor):
    try:
        if sensor:
            temperature = sensor.temperature
            humidity = sensor.relative_humidity
            return temperature, humidity
        else:
            return None, None
    except Exception as e:
        print(f"Error reading AHT20 sensor: {e}")
        return None, None

def read_temp_raw(device_file):
    with open(device_file, 'r') as f:
        lines = f.readlines()
    return lines

def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def read_arduino_data():
    arduino.write(b'GET_DATA\n')
    time.sleep(2) 
    if arduino.in_waiting > 0:
        data = arduino.readline().decode('utf-8').strip().split(',')
        if len(data) == 4:
            aht_temp = float(data[0])
            aht_hum = float(data[1])
            soil_moisture1 = float(data[2])
            soil_moisture2 = float(data[3])
            return aht_temp, aht_hum, soil_moisture1, soil_moisture2
    return None, None, None, None

def update_sensor_data(): #wszystkie odczyty - aktualizacja
    global temperature, humidity, aht_temp1, aht_hum1, soil_moisture1, soil_moisture2, temperature2, aht_temp2, aht_hum2
    aht20_sensor_rpi = initialize_aht20()

    while True:
        temperature_data = get_ds18b20_temperature()
        temperature = temperature_data[0] if len(temperature_data) > 0 else "N/A"
        temperature2 = temperature_data[1] if len(temperature_data) > 1 else "N/A"
        aht_temp1, aht_hum1, soil_moisture1, soil_moisture2 = read_arduino_data()
        aht_temp2, aht_hum2 = read_aht20(aht20_sensor_rpi)
        time.sleep(2)

def get_ds18b20_temperature():
    device_folders = glob.glob(BASE_DIR + '28-*')
    device_files = [folder + '/w1_slave' for folder in device_folders]
    temperature_data = []
    for device_file in device_files:
        temperature_data.append(read_temp(device_file))
    return temperature_data

def toggle_pin(pin):
    command_map = {
        1: b'TOGGLE_PIN3\n',
        2: b'TOGGLE_PIN4\n',
        3: b'TOGGLE_PIN5\n',
        4: b'TOGGLE_PIN6\n',
        5: b'TOGGLE_PIN7\n',
        6: b'TOGGLE_PIN8\n',
    }

    if pin in command_map:
        try:
            arduino.write(command_map[pin])
            return {"success": True, "message": f"Switched control!"}  
        except Exception as e:
            return {"success": False, "message": str(e)}
    else:
        return {"success": False, "message": "Can't switch!"}

temperature = "N/A"
humidity = "N/A"
temperature2 = "N/A"
aht_temp1 = "N/A"
aht_hum1 = "N/A"
soil_moisture1 = "N/A"
soil_moisture2 = "N/A"
aht_temp2 = "N/A"
aht_hum2 = "N/A"

#ENDPOINTY

@app.route('/')
def index():
    last_measurement = {
        "soil_moisture_1": soil_moisture1,
        "soil_moisture_2": soil_moisture2,
        "soil_temperature_1": temperature,  
        "soil_temperature_2": temperature2, 
        "air_humidity_1": aht_hum1,        
        "air_humidity_2": aht_hum2,        
        "air_temperature_1": aht_temp1,     
        "air_temperature_2": aht_temp2,    
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return render_template('index.html', last_measurement=last_measurement) #wyświetlanie

@app.route('/measurements')
def measurements():
      return jsonify({
        'soil_moisture_1': f"{soil_moisture1:.1f}",
        'soil_moisture_2': f"{soil_moisture2:.1f}",
        'soil_temperature_1': f"{temperature:.1f}",
        'soil_temperature_2': f"{temperature2:.1f}",
        'air_humidity_1': f"{aht_hum1:.1f}",
        'air_humidity_2': f"{aht_hum2:.1f}",
        'air_temperature_1': f"{aht_temp1:.1f}",
        'air_temperature_2': f"{aht_temp2:.1f}",
        'last_updated': time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
@app.route('/control_pin/<int:pin>', methods=['GET'])
def control_pin(pin):
    result = toggle_pin(pin)
    if result["success"]:
        return jsonify({"message": result["message"]})
    else:
        return jsonify({"message": result["message"]}), 400

@app.route('/history/<measurement_name>', methods=['GET'])
def get_history(measurement_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(all_measurements)")
        columns = [info[1] for info in cursor.fetchall()]
        if measurement_name not in columns:
            return jsonify({"error": "Measurement not found"}), 404
        query = f"SELECT timestamp, {measurement_name} FROM all_measurements ORDER BY timestamp DESC LIMIT 100"
        cursor.execute(query)
        results = cursor.fetchall()
        history = [{"timestamp": row[0], "value": row[1]} for row in results]
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/check_temperature', methods=['POST'])
def check_temperature():
    try:

        data = request.get_json()
        set_temp = data.get('setTemp')
        set_humi = data.get('setHumi') 
        set_moist = data.get('setMoist')  
        set_temp=float(set_temp)
        set_humi=float(set_humi)
        set_moist=float(set_moist)
    
        global aht_temp1  
        if aht_temp1 is None or aht_temp1 == "N/A":
            return jsonify({"status": "error", "message": "Temperature data is unavailable."}), 400

        current_temp = aht_temp1  

        if current_temp < set_temp - 1:
            toggle_pin(1)  
            print("Temperature is below threshold. Monitoring until it stabilizes...")
            while current_temp < set_temp + 0.5:
                current_temp = aht_temp1  
            toggle_pin(1)  
            message = f"Warning: Temperature below set threshold! Current: {current_temp:.2f}C. Pin toggled."
            status = "low_temperature"
        elif current_temp > set_temp + 1:
            toggle_pin(3)  
            toggle_pin(4)  
            toggle_pin(2)  
            print("Temperature is above threshold. Monitoring until it stabilizes...")
            while current_temp > set_temp - 0.5:
                current_temp = aht_temp1  
            toggle_pin(3)  
            toggle_pin(4)  
            toggle_pin(2) 
            message = f"Warning: Temperature above set threshold! Current: {current_temp:.2f}C. Pins toggled."
            status = "high_temperature"
        else:
            message = f"Temperature is within the set range: {current_temp:.2f}C."
            status = "safe"
            
        current_moist = soil_moisture1
        if(current_moist<set_moist):
            toggle_pin(5)
            time.sleep(6)
            toggle_pin(5)
        current_humi = aht_hum1
        if(current_humi<set_humi):
            toggle_pin(6)
            time.sleep(30)
            toggle_pin(6)
        elif(current_humi>set_humi+15):
            toggle_pin(3)  
            toggle_pin(4) 
            toggle_pin(2)  
            time.sleep(60)
            toggle_pin(3)  
            toggle_pin(4)  
            toggle_pin(2) 
            
        return jsonify({"status": status, "message": message, "current_temperature": current_temp})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/get_graph_data', methods=['GET'])
def get_graph_data():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        query = '''
            SELECT 
                timestamp,
                (soil_moisture_1 + soil_moisture_2) / 2 AS avg_soil_moisture,
                (soil_temperature_1 + soil_temperature_2) / 2 AS avg_soil_temperature,
                (air_humidity_1 + air_humidity_2) / 2 AS avg_air_humidity,
                (air_temperature_1 + air_temperature_2) / 2 AS avg_air_temperature
            FROM all_measurements
            ORDER BY timestamp DESC
            LIMIT 150
        '''
        cursor.execute(query)
        results = cursor.fetchall()

        data = {
            "timestamps": [row[0] for row in results],
            "avg_soil_moisture": [row[1] for row in results],
            "avg_soil_temperature": [row[2] for row in results],
            "avg_air_humidity": [row[3] for row in results],
            "avg_air_temperature": [row[4] for row in results]
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


init_db()
sensor_thread = threading.Thread(target=update_sensor_data)
sensor_thread.daemon = True
sensor_thread.start()

db_thread = threading.Thread(target=save_to_db)
db_thread.daemon = True
db_thread.start()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
