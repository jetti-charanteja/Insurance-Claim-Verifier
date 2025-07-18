import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import csv
import db_config
import claim_logic

# Connect to database
conn = db_config.get_connection()
cursor = conn.cursor()

# Initialize Tkinter window
root = tk.Tk()
root.title("Insurance Claim Verifier")
root.state('zoomed')
root.configure(bg="#F9FAFC")

font_label = ("Segoe UI", 12)
font_entry = ("Segoe UI", 11)
font_button = ("Segoe UI", 12, "bold")

fields = {}

# Header
tk.Label(root, text="Insurance Claim Verifier", font=("Segoe UI", 22, "bold"), fg="#0A3D62", bg="#F9FAFC").pack(pady=20)

# Form frame
form_frame = tk.Frame(root, bg="#F9FAFC")
form_frame.pack(pady=10)

# Status label
status_label = tk.Label(root, text="", font=("Segoe UI", 10), bg="#F9FAFC", fg="green")
status_label.pack()

def label_entry(field_name, row):
    tk.Label(form_frame, text=field_name + ":", font=font_label, bg="#F9FAFC", anchor="w").grid(row=row, column=0, sticky="e", pady=10, padx=20)
    entry = tk.Entry(form_frame, font=font_entry, width=35, relief="solid", bd=1, highlightbackground="#CCCCCC")
    entry.grid(row=row, column=1, pady=10, padx=20, ipady=5)
    fields[field_name] = entry

# Input fields
label_entry("Name", 0)
label_entry("Email", 1)
label_entry("Policy Number", 2)
label_entry("Policy Type", 3)
label_entry("Policy Expiry (YYYY-MM-DD)", 4)
label_entry("Coverage Amount", 5)
label_entry("Claim Amount", 6)
label_entry("Claim Reason", 7)

# Available Limit display
available_limit_label = tk.Label(root, text="Available Claim Limit: ₹0.00", font=("Segoe UI", 12, "italic"), bg="#F9FAFC", fg="#333333")
available_limit_label.pack(pady=5)

# PDF Generator
def generate_pdf(user_data, claim_data, result):
    os.makedirs("reports", exist_ok=True)
    file_name = f"reports/Claim_Report_{user_data['name'].replace(' ', '_')}.pdf"
    c = canvas.Canvas(file_name, pagesize=letter)
    c.setFont("Helvetica", 12)

    y = 750
    c.drawString(50, y, "Insurance Claim Verification Report")
    y -= 30

    c.drawString(50, y, "User Details:")
    y -= 20
    for key, value in user_data.items():
        c.drawString(70, y, f"{key}: {value}")
        y -= 20

    y -= 10
    c.drawString(50, y, "Claim Details:")
    y -= 20
    for key, value in claim_data.items():
        c.drawString(70, y, f"{key}: {value}")
        y -= 20

    y -= 10
    c.drawString(50, y, f"Verification Result: {result}")
    c.save()

    if os.path.exists(file_name):
        messagebox.showinfo("Success", f"PDF saved as '{file_name}' in 'reports/' folder.")
    else:
        messagebox.showerror("Error", "Failed to save PDF.")

# Main function
def register_and_claim():
    try:
        name = fields["Name"].get()
        email = fields["Email"].get()
        policy_number = fields["Policy Number"].get()
        policy_type = fields["Policy Type"].get()
        expiry_str = fields["Policy Expiry (YYYY-MM-DD)"].get()
        coverage_str = fields["Coverage Amount"].get()
        claim_amt_str = fields["Claim Amount"].get()
        reason = fields["Claim Reason"].get()

        if not all([name, email, policy_number, policy_type, expiry_str, coverage_str, claim_amt_str, reason]):
            messagebox.showerror("Input Error", "All fields are required.")
            return

        if '@' not in email or '.' not in email:
            messagebox.showerror("Invalid Email", "Please enter a valid email address.")
            return

        expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()
        if expiry < datetime.now().date():
            messagebox.showerror("Policy Expired", "The policy has expired. Claim cannot be submitted.")
            return
        coverage = float(coverage_str)
        claim_amt = float(claim_amt_str)

        if claim_amt > coverage:
            messagebox.showwarning("Warning", "Claim amount exceeds coverage.")

        proceed = messagebox.askyesno("Confirm Submission", "Are you sure you want to submit this claim?")
        if not proceed:
            return

        # Submit to DB with available_claim_limit initialized to coverage
        cursor.execute("""
            INSERT INTO customers (name, email, policy_number, policy_type, policy_expiry, coverage_amount, available_claim_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, policy_number, policy_type, expiry, coverage, coverage))
        conn.commit()
        user_id = cursor.lastrowid

        claim_date = datetime.now().date()
        cursor.execute("""
            INSERT INTO claims (user_id, claim_date, claim_amount, claim_reason)
            VALUES (%s, %s, %s, %s)
        """, (user_id, claim_date, claim_amt, reason))
        conn.commit()

        # Deduct claim amount from available_claim_limit
        cursor.execute("""
            UPDATE customers SET available_claim_limit = available_claim_limit - %s WHERE id = %s
        """, (claim_amt, user_id))
        conn.commit()

        # Fetch updated available_claim_limit
        cursor.execute("SELECT available_claim_limit FROM customers WHERE id = %s", (user_id,))
        new_limit = cursor.fetchone()[0]
        available_limit_label.config(text=f"Available Claim Limit: ₹{new_limit:.2f}")

        result = claim_logic.verify_claim(user_id, claim_amt)

        user_data = {
            "name": name,
            "email": email,
            "policy_number": policy_number,
            "policy_type": policy_type,
            "policy_expiry": expiry,
            "coverage_amount": coverage
        }

        claim_data = {
            "claim_date": claim_date,
            "claim_amount": claim_amt,
            "claim_reason": reason
        }

        # Export to CSV
        with open("claim_records.csv", "a", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)
            writer.writerow([name, email, policy_number, claim_amt, claim_date, result])

        generate_pdf(user_data, claim_data, result)
        status_label.config(text="Claim submitted successfully!")
        messagebox.showinfo("Claim Status", result)

        # Reset entries
        for entry in fields.values():
            entry.delete(0, tk.END)

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="")

# Function to check available claims by email
def check_claim_by_email():
    email = fields["Email"].get()
    if not email:
        messagebox.showerror("Input Error", "Please enter an email address.")
        return

    try:
        cursor.execute("""
            SELECT c.name, cl.claim_date, cl.claim_amount, cl.claim_reason, c.available_claim_limit
            FROM customers c
            JOIN claims cl ON c.id = cl.user_id
            WHERE c.email = %s
        """, (email,))
        results = cursor.fetchall()

        if results:
            result_text = "Claim(s) for {}:\n\n".format(email)
            for row in results:
                result_text += f"Name: {row[0]}\nDate: {row[1]}\nAmount: {row[2]}\nReason: {row[3]}\nAvailable Limit: ₹{row[4]:.2f}\n---\n"
            messagebox.showinfo("Available Claims", result_text)
        else:
            messagebox.showinfo("No Claims Found", f"No claims found for {email}.")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Submit Button
submit_btn = tk.Button(root, text="Submit Claim", command=register_and_claim,
                       bg="#007BFF", fg="white", font=font_button, width=20,
                       activebackground="#0056b3", cursor="hand2", relief="flat")
submit_btn.pack(pady=10)

# Check Claims Button
check_btn = tk.Button(root, text="Check Available Claims", command=check_claim_by_email,
                      bg="#28a745", fg="white", font=font_button, width=25,
                      activebackground="#1e7e34", cursor="hand2", relief="flat")
check_btn.pack(pady=10)

# Run app
root.mainloop()