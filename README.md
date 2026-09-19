# Delivery & Restaurant Analytics System

A desktop-based restaurant and food-delivery management and analytics system built using Python, Tkinter, MySQL/MariaDB, SQL, Pandas, NumPy, Matplotlib, and Seaborn.

The project combines database management, CRUD operations, SQL analytics, data analysis, visualization, and report exporting into a single application.

---

## Project Overview

The Delivery & Restaurant Analytics System manages the major entities involved in a food-delivery platform, including customers, addresses, restaurants, menu items, orders, riders, deliveries, payments, and reviews.

The application provides a graphical interface for managing database records and an analytics dashboard for analyzing business performance.

The overall workflow is:

```text
Database
    ↓
SQL Queries
    ↓
Data Extraction
    ↓
Pandas Analysis
    ↓
Visualization
    ↓
Report Export
```

---

## Features

### Database Management

The system uses a relational MySQL/MariaDB database containing 10 main tables:

- Customers
- Addresses
- Restaurants
- Menu Items
- Orders
- Order Items
- Riders
- Deliveries
- Payments
- Reviews

### Graphical User Interface

The application is built using Python Tkinter and provides a graphical interface for interacting with the database.

Users can manage different entities of the food-delivery system through the application instead of manually executing SQL queries for every operation.

### CRUD Operations

The application supports:

- Create
- Read
- Update
- Delete

operations for the supported database entities.

### Analytics Dashboard

The application includes an analytics dashboard for analyzing data stored in the database.

The analytics section provides information related to:

- Orders
- Revenue
- Restaurants
- Deliveries
- Payments
- Ratings
- Reviews
- Order statuses
- Time-based trends

### Analytics Filters

The analytics dashboard supports filtering using:

- Restaurant
- Order status
- From date
- To date

This allows users to analyze specific subsets of the available data.

### SQL Analytics

SQL is used to extract and analyze information directly from the relational database.

The project demonstrates practical use of:

- SELECT
- WHERE
- JOIN
- GROUP BY
- ORDER BY
- HAVING
- Aggregate functions
- CASE statements
- Subqueries
- Date-based filtering
- Data aggregation

### Pandas Analysis

Database query results can be loaded into Pandas DataFrames for further analysis.

Pandas is used for:

- Filtering
- Grouping
- Aggregation
- Data transformation
- Trend analysis
- Statistical summaries

### Data Visualization

Matplotlib and Seaborn are used to visualize analytical results.

Visualizations can be used to analyze:

- Revenue trends
- Order trends
- Restaurant performance
- Ratings
- Delivery performance
- Payment distribution

### Report Export

Analytical results can be exported for further use.

Supported formats include:

- CSV
- Excel

Excel export is handled using `openpyxl`.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Tkinter | GUI development |
| MySQL / MariaDB | Relational database |
| SQL | Database operations and analytics |
| Pandas | Data analysis |
| NumPy | Numerical operations |
| Matplotlib | Data visualization |
| Seaborn | Statistical visualization |
| OpenPyXL | Excel export |
| XAMPP | Local database environment |

---

## Database Design

The system contains the following 10 main tables:

```text
customers
addresses
restaurants
menu_items
orders
order_items
riders
deliveries
payments
reviews
```

### Entity Relationship Diagram

The major relationships between the entities are:

```text
CUSTOMERS
    |
    +------ ADDRESSES
    |
    +------ ORDERS
                |
                +------ ORDER_ITEMS ------ MENU_ITEMS ------ RESTAURANTS
                |
                +------ DELIVERIES ------ RIDERS
                |
                +------ PAYMENTS
                |
                +------ REVIEWS
                           |
                           +------ CUSTOMERS
                           |
                           +------ RESTAURANTS
```

A detailed Mermaid ER diagram is available in:

```text
database/ER_DIAGRAM.md
```

### Database Relationships

- A customer can have multiple addresses.
- A customer can place multiple orders.
- A restaurant can have multiple menu items.
- A restaurant can receive multiple orders.
- An order can contain multiple order items.
- A menu item can appear in multiple order items.
- Orders are associated with delivery records.
- A rider can handle multiple deliveries.
- Orders can have associated payment records.
- Orders can have associated reviews.
- Customers can submit reviews.
- Restaurants can receive reviews.
- Orders can use saved customer addresses.

---

## Project Structure

```text
delivery_analytics/
│
├── app/
│   ├── gui/
│   │   ├── __init__.py
│   │   └── app.py
│   │
│   ├── database.py
│   └── main.py
│
├── database/
│   ├── schema.sql
│   ├── sample_data.sql
│   └── ER_DIAGRAM.md
│
├── exports/
│
├── screenshots/
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Database Setup

### Prerequisites

Make sure the following are installed:

- Python
- XAMPP
- MySQL/MariaDB

### 1. Start XAMPP

Open XAMPP Control Panel and start the MySQL service.

The current application configuration uses:

```text
Host: localhost
Port: 3307
Database: delivery_analytics
User: root
```

If your MySQL configuration is different, update the connection settings in:

```text
app/database.py
```

### 2. Create the Database

The database structure is provided in:

```text
database/schema.sql
```

Import this file into MySQL/MariaDB using phpMyAdmin or the MySQL/MariaDB command line.

The schema creates the required tables and relationships.

### 3. Load Sample Data

After creating the database structure, import:

```text
database/sample_data.sql
```

This file contains the sample/demo records used by the application.

---

## Python Setup

From the project root directory, install the required packages:

```bash
pip install -r requirements.txt
```

The main dependencies are:

```text
mysql-connector-python
pandas
numpy
matplotlib
seaborn
openpyxl
```

---

## Running the Application

From the project root directory:

```bash
python app/main.py
```

The Tkinter application will launch.

---

## Analytics Workflow

The application's analytics workflow can be represented as:

```text
              MySQL / MariaDB
                     |
                     ↓
                SQL Queries
                     |
                     ↓
             Analytics Results
                     |
           +---------+---------+
           |                   |
           ↓                   ↓
        Pandas             Visualization
           |                   |
           +---------+---------+
                     |
                     ↓
               Report Export
                /          \
              CSV          Excel
```

---

## Example Business Questions

The analytics system can be used to investigate questions such as:

- How many orders were placed?
- What is the total revenue?
- How are orders distributed by status?
- Which restaurants received orders?
- How does revenue change over time?
- What are the restaurant ratings?
- How are payments distributed by payment method?
- How does delivery distance vary?
- How does order activity change over time?
- What patterns can be identified from the available order data?

---

## Data Analysis Workflow

The project demonstrates a practical data-analysis pipeline:

```text
Database
    ↓
SQL
    ↓
Data Extraction
    ↓
Pandas
    ↓
Data Cleaning / Transformation
    ↓
Analysis
    ↓
Visualization
    ↓
CSV / Excel Export
```

---

## SQL Concepts Demonstrated

The project provides practical usage of:

```text
SELECT
WHERE
JOIN
INNER JOIN
LEFT JOIN
GROUP BY
ORDER BY
HAVING
CASE
Aggregate Functions
Subqueries
Date Functions
Filtering
Data Aggregation
```

---

## Python Concepts Demonstrated

The application demonstrates:

- Python functions
- Classes and objects
- Tkinter GUI development
- Database connectivity
- Exception handling
- SQL execution from Python
- Pandas DataFrames
- Data processing
- Matplotlib visualization
- Seaborn visualization
- File export

---

## Sample Data

The project includes sample/demo data for development and demonstration purposes.

The sample data is stored in:

```text
database/sample_data.sql
```

Before publishing the repository publicly, ensure that all sample records are fictional or otherwise appropriate to distribute.

---

## Future Improvements

Possible future improvements include:

- User authentication
- Role-based access control
- Advanced customer analytics
- Predictive demand analysis
- Delivery-time prediction
- Restaurant recommendation system
- More interactive visualizations
- Automated report generation
- Cloud database deployment
- Web-based version
- Real-time order tracking
- API integration

---

## Learning Outcomes

This project provides practical experience with:

- Relational database design
- SQL
- Database relationships
- Python database connectivity
- GUI development
- CRUD applications
- Data analysis with Pandas
- Numerical analysis with NumPy
- Data visualization
- Business analytics
- CSV and Excel reporting
- Project organization

---

## Author

Developed as a practical project combining:

```text
Python
+
SQL
+
Database Management
+
Data Analysis
+
Data Visualization
+
GUI Development
```

---

## License

This project is intended for educational and portfolio purposes.