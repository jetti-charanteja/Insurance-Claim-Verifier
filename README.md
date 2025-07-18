# Automated Insurance Claim Verifier

**Author**: Jetti Charan Teja Naga Sai  
**Technologies**: Python, Tkinter, MySQL, ReportLab

---

## Overview

A desktop GUI application to automate insurance claim verification. It validates user-submitted claim details against a MySQL database and generates downloadable PDF reports.

---

## Features

- GUI-based user input (Tkinter)
- Real-time insurance claim validation
- MySQL database integration
- Auto-generated PDF reports (ReportLab)

---

## Technologies Used

- Python 3.x
- Tkinter
- MySQL
- ReportLab

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/jetti-charanteja/insurance-claim-verifier.git
cd insurance-claim-verifier
```

### 2. Install required packages
```bash
pip install mysql-connector-python reportlab
```

### 3. Set up the MySQL database

- Create a database and required tables
- Configure credentials in `db_config.py`

### 4. Run the application
```bash
python main.py
```

---

## File Structure

```
insurance-claim-verifier/
├── main.py               # Main GUI logic
├── db_config.py          # MySQL connection config
├── README.md             # Project documentation
└── requirements.txt      # Required dependencies
```

---

## Requirements

- Python 3.x
- MySQL Server
- Required Python packages (in `requirements.txt`):
  - mysql-connector-python
  - reportlab

---

## Author

Jetti Charan Teja Naga Sai  
Email: [jcharanteja11@gmail.com]
