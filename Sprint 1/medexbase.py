import os
from dotenv import load_dotenv
import smtplib
from datetime import datetime
import time
from typing import Optional

class Patient:
    def __init__(self):
        self.name = ""
        self.id = ""
        self.email = ""
        self.medications = []
        self.emergency_contact = {}
        self.doctor = ""

class MedicationInfo:
    def __init__(self, name: str, dosage_amount: str, dosage_time: str, total_doses: int):
        self.name = name
        self.dosage_amount = dosage_amount
        self.dosage_time = dosage_time
        self.total_doses = total_doses
        self.doses_remaining = total_doses
        self.last_notification_sent = None

class NotificationSystem:
    def __init__(self):
        load_dotenv()
        self.sender_email = "personvcu@gmail.com"
        self.password = os.getenv("EMAIL_PASSWORD")
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds

    def send_notification(self, patient: Patient, med: MedicationInfo, notification_type: str) -> bool:
        """Send notification with retry mechanism"""
        subject = f"Medication Alert: {med.name}"
        
        # Create message based on notification type
        if notification_type == "reminder":
            message = (f"Medication Reminder for {patient.name}\n\n"
                      f"Time to take: {med.dosage_time}\n"
                      f"Medication: {med.name}\n"
                      f"Dosage Amount: {med.dosage_amount}\n"
                      f"Doses Remaining: {med.doses_remaining}\n\n"
                      f"Emergency Contact: {patient.emergency_contact['name']} - {patient.emergency_contact['phone']}\n"
                      f"Doctor: {patient.doctor}")
        elif notification_type == "low_dosage":
            message = (f"LOW DOSAGE ALERT for {patient.name}\n\n"
                      f"Medication: {med.name}\n"
                      f"Only {med.doses_remaining} doses remaining!\n\n"
                      f"Please refill your prescription soon or talk to your doctor: {patient.doctor}")
        elif notification_type == "no_dosage":
            message = (f"URGENT: NO DOSES REMAINING for {patient.name}\n\n"
                      f"Medication: {med.name}\n"
                      f"You have run out of doses for this medication.\n"
                      f"Please get another prescription, update the program, or see your doctor: {patient.doctor}")

        # Attempt to send email with retry mechanism
        for attempt in range(self.retry_attempts):
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(self.sender_email, self.password)
                
                text = f"Subject: {subject}\n\n{message}"
                server.sendmail(self.sender_email, patient.email, text)
                print(f"Email sent successfully to {patient.email}")
                server.quit()
                return True

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    print(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                server.quit()

        print(f"WARNING: Failed to deliver notification to {patient.email} after {self.retry_attempts} attempts")
        return False

class PatientDirectory:
    def __init__(self):
        self.patients = {}
        self.notification_system = NotificationSystem()

    def add_patient(self):
        patient = Patient()
        
        patient.name = input("Enter patient name: ")
        patient.email = input("Enter patient email: ")
        
        while True:
            patient.id = input("Enter patient ID: ")
            if patient.id not in self.patients:
                break
            print("ID already exists. Please enter a unique ID.")

        while True:
            add_med = input("Would you like to add a medication? (yes/no): ").lower()
            if add_med != 'yes':
                break
                
            med_name = input("Enter medication name: ")
            dosage_amount = input("Enter dosage amount per dose: ")
            dosage_time = input("Enter dosage time (e.g., '8:00 AM, 8:00 PM'): ")
            total_doses = int(input("Enter total number of doses in prescription: "))
            
            med = MedicationInfo(med_name, dosage_amount, dosage_time, total_doses)
            patient.medications.append(med)

        print("\nEmergency Contact Information:")
        contact_name = input("Enter emergency contact name: ")
        contact_phone = input("Enter emergency contact phone: ")
        patient.emergency_contact = {
            "name": contact_name,
            "phone": contact_phone
        }

        patient.doctor = input("Enter doctor's name: ")

        self.patients[patient.id] = patient
        print("\nPatient added successfully!")

    def record_medication_taken(self, patient_id: str, med_index: int):
        """Record that a medication dose was taken and handle notifications"""
        if patient_id not in self.patients:
            print("Patient not found!")
            return

        patient = self.patients[patient_id]
        if med_index >= len(patient.medications):
            print("Invalid medication index!")
            return

        med = patient.medications[med_index]
        
        if med.doses_remaining > 0:
            med.doses_remaining -= 1
            print(f"Recorded dose taken. {med.doses_remaining} doses remaining.")

            # Send regular reminder with medication details
            self.notification_system.send_notification(patient, med, "reminder")

            # Check for low dosage (5 doses remaining)
            if med.doses_remaining == 5:
                if not self.notification_system.send_notification(patient, med, "low_dosage"):
                    print("WARNING: Failed to send low dosage alert!")

            # Check for no doses remaining
            if med.doses_remaining == 0:
                if not self.notification_system.send_notification(patient, med, "no_dosage"):
                    print("WARNING: Failed to send no dosage alert!")
        else:
            print("No doses remaining! Please refill prescription.")

    def display_patient(self, patient_id):
        if patient_id in self.patients:
            patient = self.patients[patient_id]
            print("\nPatient Information:")
            print(f"Name: {patient.name}")
            print(f"ID: {patient.id}")
            print(f"Email: {patient.email}")
            print("\nMedications:")
            if patient.medications:
                for i, med in enumerate(patient.medications):
                    print(f"{i+1}. {med.name}")
                    print(f"   Dosage: {med.dosage_amount}")
                    print(f"   Time: {med.dosage_time}")
                    print(f"   Doses Remaining: {med.doses_remaining}")
            else:
                print("No medications listed")
            print(f"\nEmergency Contact: {patient.emergency_contact['name']}")
            print(f"Emergency Phone: {patient.emergency_contact['phone']}")
            print(f"Doctor: {patient.doctor}")
        else:
            print("Patient not found!")

    def run(self):
        while True:
            print("\nPatient Directory Menu:")
            print("1. Add new patient")
            print("2. Display patient information")
            print("3. Record medication taken")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == "1":
                self.add_patient()
            elif choice == "2":
                patient_id = input("Enter patient ID to display: ")
                self.display_patient(patient_id)
            elif choice == "3":
                patient_id = input("Enter patient ID: ")
                if patient_id in self.patients:
                    self.display_patient(patient_id)
                    med_index = int(input("Enter medication number to record: ")) - 1
                    self.record_medication_taken(patient_id, med_index)
                else:
                    print("Patient not found!")
            elif choice == "4":
                print("Exiting program...")
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    directory = PatientDirectory()
    directory.run()