class RideManager {
    constructor() {
        this.map = null;
        this.pickupMarker = null;
        this.dropoffMarker = null;
        this.driverMarker = null;
        this.pickupRoute = null;
        this.rideRoute = null;
        this.currentRideId = null;
        this.selectedVehicle = 'bike';
        
        this.defaultLocation = {
            lat: 28.5456,
            lng: 77.1926,
            zoom: 15
        };
        
        this.init();
    }

    init() {
        this.map = L.map('map').setView(
            [this.defaultLocation.lat, this.defaultLocation.lng], 
            this.defaultLocation.zoom
        );
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        this.setupEventListeners();
        this.setupVehicleSelection();

        // Set initial pickup marker
        this.handleLocationSet('pickup', L.latLng(this.defaultLocation.lat, this.defaultLocation.lng));
    }

    setupEventListeners() {
        document.getElementById('setPickup').addEventListener('click', () => this.setLocation('pickup'));
        document.getElementById('setDropoff').addEventListener('click', () => this.setLocation('dropoff'));
        document.getElementById('setDriver').addEventListener('click', () => this.setLocation('driver'));
        document.getElementById('calculateRide').addEventListener('click', () => this.calculateRide());
        document.getElementById('confirmBooking')?.addEventListener('click', () => this.startRide());
    }

    handleLocationSet(type, latlng) {
        const markerColors = {
            pickup: 'green',
            dropoff: 'red',
            driver: 'blue'
        };

        const icon = L.icon({
            iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${markerColors[type]}.png`,
            iconSize: [25, 41],
            iconAnchor: [12, 41]
        });

        // Remove existing marker if any
        if (this[`${type}Marker`]) {
            this.map.removeLayer(this[`${type}Marker`]);
        }

        // Create new marker
        this[`${type}Marker`] = L.marker(latlng, {icon}).addTo(this.map);

        // Update coordinates display
        const coordsElement = document.getElementById(`${type}Coords`);
        if (coordsElement) {
            coordsElement.textContent = `${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`;
        }
    }

    setLocation(type) {
        const button = document.getElementById(`set${type.charAt(0).toUpperCase() + type.slice(1)}`);
        if (button) {
            button.textContent = 'Click on map';
            button.style.backgroundColor = '#e74c3c';
        }

        const clickHandler = (e) => {
            this.handleLocationSet(type, e.latlng);
            if (button) {
                button.textContent = 'Set on Map';
                button.style.backgroundColor = '';
            }
            this.map.off('click', clickHandler);
        };

        this.map.once('click', clickHandler);
    }

    async startRide() {
        try {
            console.log('Starting ride...');
            
            // Show loading state on button
            const button = document.getElementById('confirmBooking');
            if (!button) {
                console.error('Confirm booking button not found');
                return;
            }
            
            button.disabled = true;
            button.innerHTML = '<span class="loading"></span> Starting Ride...';

            // Create or get status container
            let statusContainer = document.getElementById('rideStatusContainer');
            if (!statusContainer) {
                statusContainer = document.createElement('div');
                statusContainer.id = 'rideStatusContainer';
                
                // Look for the correct container - 'fare-details' instead of 'fare-details'
                const fareDetails = document.querySelector('.fare-details, #fareDetails');  // Try both class and ID
                if (!fareDetails) {
                    // If fare details not found, append to the sidebar
                    const sidebar = document.querySelector('.sidebar');
                    if (sidebar) {
                        sidebar.appendChild(statusContainer);
                    } else {
                        throw new Error('Could not find container for status updates');
                    }
                } else {
                    fareDetails.parentNode.insertBefore(statusContainer, fareDetails.nextSibling);
                }
            }

            // Create or update status message
            let statusDiv = document.getElementById('rideStatus');
            if (!statusDiv) {
                statusDiv = document.createElement('div');
                statusDiv.id = 'rideStatus';
                statusContainer.appendChild(statusDiv);
            }
            
            statusDiv.innerHTML = `
                <div class="status-message">
                    <span class="loading"></span>
                    Driver is on the way to pickup location...
                </div>
            `;

            // Start driver simulation
            if (this.pickupRoute && this.driverMarker) {
                await this.simulateDriverToPickup();
            } else {
                throw new Error('Route or driver marker not initialized');
            }

        } catch (error) {
            console.error('Failed to start ride:', error);
            alert('Failed to start ride: ' + error.message);
            
            // Reset button state
            const button = document.getElementById('confirmBooking');
            if (button) {
                button.disabled = false;
                button.innerHTML = 'Confirm Booking';
            }
        }
    }

    simulateDriverToPickup() {
        return new Promise((resolve) => {
            if (!this.pickupRoute || !this.driverMarker) {
                console.error('Route or driver marker not found');
                resolve(); // Resolve to prevent hanging
                return;
            }

            console.log('Starting driver simulation...'); // Debug log
            
            let progress = 0;
            const speed = this.selectedVehicle === 'bike' ? 40 : 60; // km/h
            const routePoints = this.pickupRoute.getLatLngs();
            
            this.driverInterval = setInterval(() => {
                progress += speed / 3600;
                
                if (progress >= 1) {
                    clearInterval(this.driverInterval);
                    this.driverMarker.setLatLng(this.pickupMarker.getLatLng());
                    this.arrivedAtPickup();
                    resolve();
                } else {
                    const pointIndex = Math.floor(progress * routePoints.length);
                    if (routePoints[pointIndex]) {
                        this.driverMarker.setLatLng(routePoints[pointIndex]);
                    }
                }
            }, 1000);
        });
    }

    setupVehicleSelection() {
        const bikeOption = document.querySelector('[data-vehicle="bike"]');
        const carOption = document.querySelector('[data-vehicle="car"]');

        if (bikeOption && carOption) {
            bikeOption.addEventListener('click', () => this.selectVehicle('bike'));
            carOption.addEventListener('click', () => this.selectVehicle('car'));
            
            // Set bike as default selected vehicle
            this.selectVehicle('bike');
        }
    }

    selectVehicle(type) {
        this.selectedVehicle = type;
        
        // Update UI
        document.querySelectorAll('.vehicle-option').forEach(option => {
            option.classList.remove('active');
            if (option.dataset.vehicle === type) {
                option.classList.add('active');
            }
        });
    }

    async calculateRide() {
        if (!this.pickupMarker || !this.dropoffMarker || !this.driverMarker) {
            alert('Please set all locations first!');
            return;
        }

        try {
            // Show loading state
            const button = document.getElementById('calculateRide');
            button.disabled = true;
            button.innerHTML = '<span class="loading"></span> Calculating...';

            const response = await fetch('/api/calculate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({
                    pickup: {
                        lat: this.pickupMarker.getLatLng().lat,
                        lng: this.pickupMarker.getLatLng().lng
                    },
                    dropoff: {
                        lat: this.dropoffMarker.getLatLng().lat,
                        lng: this.dropoffMarker.getLatLng().lng
                    },
                    driver: {
                        lat: this.driverMarker.getLatLng().lat,
                        lng: this.driverMarker.getLatLng().lng
                    },
                    vehicle_type: this.selectedVehicle
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.currentRideId = data.data.ride_id;
                this.displayRideDetails(data.data);
                this.drawRoutes(data.data);
            } else {
                throw new Error(data.message);
            }
        } catch (error) {
            console.error('Failed to calculate ride:', error);
            alert('Failed to calculate ride: ' + error.message);
        } finally {
            // Reset button state
            const button = document.getElementById('calculateRide');
            button.disabled = false;
            button.innerHTML = '<span class="material-icons">route</span> Show Route & Fare';
        }
    }

    displayRideDetails(data) {
        // Calculate ETA based on distance and speed
        const speed = document.querySelector('.vehicle-option.active').dataset.vehicle === 'bike' ? 40 : 60; // km/h
        const timeInHours = data.distance / speed;
        const timeInMinutes = Math.round(timeInHours * 60);

        document.getElementById('rideDistance').textContent = `${data.distance.toFixed(2)} km`;
        document.getElementById('rideTime').textContent = `${timeInMinutes} min`;
        document.getElementById('rideCost').textContent = `₹${data.cost.toFixed(2)}`;
        
        // Show ride details section
        document.getElementById('rideDetails').style.display = 'block';
        
        // Scroll to ride details
        document.getElementById('rideDetails').scrollIntoView({ behavior: 'smooth' });
    }

    drawRoutes(data) {
        // Clear existing routes
        if (this.pickupRoute) this.map.removeLayer(this.pickupRoute);
        if (this.rideRoute) this.map.removeLayer(this.rideRoute);

        // Draw route from driver to pickup (blue)
        const pickupCoords = data.pickup_route.geometry.map(coord => [coord[1], coord[0]]);
        this.pickupRoute = L.polyline(pickupCoords, {
            color: '#276EF1',
            weight: 4,
            opacity: 0.8,
            dashArray: '10, 10'  // Dashed line for driver route
        }).addTo(this.map);

        // Draw route from pickup to dropoff (black)
        const rideCoords = data.ride_route.geometry.map(coord => [coord[1], coord[0]]);
        this.rideRoute = L.polyline(rideCoords, {
            color: '#000000',
            weight: 4,
            opacity: 0.8
        }).addTo(this.map);

        // Fit map to show all routes
        const bounds = L.featureGroup([this.pickupRoute, this.rideRoute]).getBounds();
        this.map.fitBounds(bounds, { padding: [50, 50] });
    }

    arrivedAtPickup() {
        console.log('Driver arrived at pickup'); // Debug log
        
        const statusDiv = document.getElementById('rideStatus');
        if (!statusDiv) return;

        statusDiv.innerHTML = `
            <div class="status-message">
                <span class="material-icons">check_circle</span>
                Driver has arrived at pickup location
            </div>
            <button id="startJourneyBtn" class="primary-btn">
                Start Journey
            </button>
        `;

        document.getElementById('startJourneyBtn')?.addEventListener('click', () => this.startJourney());
    }

    async startJourney() {
        try {
            const statusDiv = document.getElementById('rideStatus');
            statusDiv.innerHTML = 'Journey in progress...';
            
            let progress = 0;
            const speed = this.selectedVehicle === 'bike' ? 40 : 60; // km/h
            const routePoints = this.rideRoute.getLatLngs();
            
            this.journeyInterval = setInterval(() => {
                progress += speed / 3600;
                
                if (progress >= 1) {
                    clearInterval(this.journeyInterval);
                    this.driverMarker.setLatLng(this.dropoffMarker.getLatLng());
                    this.completeRide();
                } else {
                    const pointIndex = Math.floor(progress * routePoints.length);
                    if (routePoints[pointIndex]) {
                        this.driverMarker.setLatLng(routePoints[pointIndex]);
                    }
                }
            }, 1000);
            
        } catch (error) {
            console.error('Failed during journey:', error);
            alert('Failed during journey: ' + error.message);
        }
    }

    completeRide() {
        const statusDiv = document.getElementById('rideStatus');
        statusDiv.innerHTML = 'Ride Completed! Please rate your experience.';
        
        // Show rating interface
        const ratingDiv = document.createElement('div');
        ratingDiv.className = 'rating-container';
        ratingDiv.innerHTML = `
            <div class="rating">
                <span class="star" data-rating="1">★</span>
                <span class="star" data-rating="2">★</span>
                <span class="star" data-rating="3">★</span>
                <span class="star" data-rating="4">★</span>
                <span class="star" data-rating="5">★</span>
            </div>
            <button class="primary-btn" id="submitRating">Submit Rating</button>
        `;
        
        statusDiv.appendChild(ratingDiv);
        
        // Add rating functionality
        const stars = ratingDiv.querySelectorAll('.star');
        stars.forEach(star => {
            star.addEventListener('click', () => {
                const rating = star.dataset.rating;
                stars.forEach(s => {
                    s.classList.toggle('active', s.dataset.rating <= rating);
                });
            });
        });
        
        // Add submit rating functionality
        document.getElementById('submitRating').addEventListener('click', () => {
            const rating = document.querySelector('.star.active:last-child')?.dataset.rating || 5;
            this.submitRating(rating);
        });
    }

    async submitRating(rating) {
        try {
            const response = await fetch(`/api/ride/${this.currentRideId}/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: JSON.stringify({ rating: parseInt(rating) })
            });

            if (response.ok) {
                alert('Thank you for your rating! Ride completed.');
                window.location.reload();
            }
        } catch (error) {
            console.error('Failed to submit rating:', error);
            alert('Failed to submit rating. Please try again.');
        }
    }

    // Add CSS for status messages
    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            #rideStatusContainer {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }

            .status-message {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
                color: #2c3e50;
            }

            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-radius: 50%;
                border-top: 3px solid #3498db;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const rideManager = new RideManager();
    rideManager.addStyles();
});
