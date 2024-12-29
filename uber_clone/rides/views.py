from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Ride
import json
import requests

def index(request):
    context = {
        'title': 'Ride Booking System',
        'description': '''
        Welcome to our Ride Booking System! Set your pickup and drop-off locations,
        choose a vehicle type, and book your ride. Bikes cost ₹3/km and cars cost ₹8/km.
        '''
    }
    return render(request, 'rides/index.html', context)

@require_http_methods(["POST"])
def calculate_ride(request):
    try:
        data = json.loads(request.body)
        
        # Create new ride
        ride = Ride.objects.create(
            pickup_lat=data['pickup']['lat'],
            pickup_lng=data['pickup']['lng'],
            dropoff_lat=data['dropoff']['lat'],
            dropoff_lng=data['dropoff']['lng'],
            driver_lat=data['driver']['lat'],
            driver_lng=data['driver']['lng'],
            vehicle_type=data['vehicle_type']
        )

        # Calculate routes using OSRM
        pickup_route = get_route(
            (ride.driver_lat, ride.driver_lng),
            (ride.pickup_lat, ride.pickup_lng)
        )
        
        ride_route = get_route(
            (ride.pickup_lat, ride.pickup_lng),
            (ride.dropoff_lat, ride.dropoff_lng)
        )

        ride.distance = ride_route['distance']
        ride.cost = ride.calculate_cost()
        ride.save()

        return JsonResponse({
            'status': 'success',
            'data': {
                'ride_id': ride.id,
                'pickup_route': pickup_route,
                'ride_route': ride_route,
                'cost': float(ride.cost),
                'distance': ride.distance
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def get_route(start, end):
    """Calculate route using OSRM."""
    url = (f"https://router.project-osrm.org/route/v1/driving/"
           f"{start[1]},{start[0]};{end[1]},{end[0]}"
           "?overview=full&geometries=geojson")
    
    response = requests.get(url)
    data = response.json()
    
    if data['code'] != 'Ok':
        raise ValueError("Unable to calculate route")
        
    route = data['routes'][0]
    return {
        'distance': route['distance'] / 1000,  # Convert to kilometers
        'duration': route['duration'],
        'geometry': route['geometry']['coordinates']
    }

@require_http_methods(["POST"])
def complete_ride(request, ride_id):
    try:
        data = json.loads(request.body)
        ride = Ride.objects.get(id=ride_id)
        ride.rating = data.get('rating')
        ride.save()
        return JsonResponse({'status': 'success'})
    except Ride.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Ride not found'
        }, status=404)

def perimeter(request):
    return render(request, 'rides/perimeter.html')
