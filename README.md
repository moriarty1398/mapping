# Ride Booking System with Perimeter Definition

A web application built with Django that combines ride booking functionality with geographic perimeter definition capabilities.

## Features

### Ride Booking
- Set pickup and drop-off locations on an interactive map
- Choose between different vehicle types (bike/car)
- Real-time fare calculation
- Driver-to-pickup simulation
- Journey simulation with status updates
- Ride rating system

### Perimeter Definition
- Interactive map interface for defining areas
- Create polygons by clicking points on the map
- Support for triangles and complex polygons
- Real-time area and perimeter calculations
- Visual feedback with markers and connecting lines
- Clear and start over functionality

## Tech Stack

- **Backend:** Django 5.0
- **Frontend:** HTML, CSS, JavaScript
- **Maps:** Leaflet.js
- **Icons:** Material Icons
- **Font:** Inter

## Installation

1. Clone the repository

2. Create and activate virtual environment

3. Install dependencies

4. Run migrations

5. Start development server

The application will be available at `http://localhost:8000`

## Usage

### Ride Booking
1. Open the main page
2. Set pickup location (default: IIT Delhi)
3. Set drop-off location by clicking on the map
4. Select vehicle type
5. Click "Show Route & Fare" to see pricing
6. Click "Confirm Booking" to start the ride simulation

### Perimeter Definition
1. Click "Define Perimeter" in the header
2. Click on the map to add points (minimum 3)
3. Click "Complete Shape" to close the perimeter
4. View area and perimeter calculations
5. Use "Clear Points" to start over

## Project Structure
uber_clone/
├── rides/
│ ├── static/
│ │ ├── css/
│ │ │ ├── style.css
│ │ │ └── perimeter.css
│ │ └── js/
│ │ ├── ride.js
│ │ └── perimeter.js
│ ├── templates/
│ │ └── rides/
│ │ ├── index.html
│ │ └── perimeter.html
│ ├── models.py
│ ├── views.py
│ └── urls.py
├── manage.py
└── requirements.txt




## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenStreetMap for map data
- Leaflet.js for map visualization
- Material Icons for UI elements
