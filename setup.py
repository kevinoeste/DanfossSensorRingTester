from flask import Flask, render_template
import sqlite3

conn = sqlite3.connect('testData.db')
print("Connected to testData.")

try:
    conn.execute("DROP TABLE IF EXISTS SensorData")
    conn.execute("CREATE TABLE SensorData(timestamp DATETIME,fx_pos FLOAT,fx_neg FLOAT,fy_pos FLOAT,fy_neg FLOAT,ax_pos FLOAT,ax_neg FLOAT, test_id INT AUTO_INCREMENT, PRIMARY KEY(test_id))")
    print("Table created.")
except:
    print("Error: Could not create table SensorData")
