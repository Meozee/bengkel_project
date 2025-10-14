# apps/master_data/models.py

from django.db import models

class Mechanic(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, blank=True)
    specialty = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"

class Vehicle(models.Model):
    # Relasi: Satu Customer bisa punya banyak Vehicle
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='vehicles')
    
    license_plate = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=100) # Merek, e.g., Toyota
    model = models.CharField(max_length=100) # Model, e.g., Avanza
    year = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.license_plate} ({self.brand} {self.model})"

class Service(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Standard price for this service")

    def __str__(self):
        return self.name
        
class Vendor(models.Model):
    name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name