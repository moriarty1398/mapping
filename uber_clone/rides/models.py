from django.db import models

class Ride(models.Model):
    VEHICLE_CHOICES = [
        ('bike', 'Bike'),
        ('car', 'Car'),
    ]
    
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    driver_lat = models.FloatField()
    driver_lng = models.FloatField()
    vehicle_type = models.CharField(max_length=4, choices=VEHICLE_CHOICES)
    distance = models.FloatField(null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    rating = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    def calculate_cost(self):
        rate = 3 if self.vehicle_type == 'bike' else 8
        return self.distance * rate
