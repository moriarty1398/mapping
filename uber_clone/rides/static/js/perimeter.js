class PerimeterManager {
    constructor() {
        this.map = null;
        this.points = [];
        this.markers = [];
        this.polygon = null;
        this.polyline = null;
        
        this.init();
    }

    init() {
        // Initialize map centered on IIT Delhi
        this.map = L.map('map').setView([28.5456, 77.1926], 15);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.map.on('click', (e) => this.addPoint(e.latlng));
        
        document.getElementById('completeShape').addEventListener('click', () => this.completeShape());
        document.getElementById('clearPoints').addEventListener('click', () => this.clearPoints());
    }

    addPoint(latlng) {
        const marker = L.marker(latlng).addTo(this.map);
        this.points.push(latlng);
        this.markers.push(marker);

        // Update polyline
        if (this.polyline) {
            this.map.removeLayer(this.polyline);
        }
        this.polyline = L.polyline(this.points, {color: 'blue'}).addTo(this.map);

        // Enable complete button if we have at least 3 points
        document.getElementById('completeShape').disabled = this.points.length < 3;

        // Update point count
        document.getElementById('pointCount').textContent = this.points.length;
    }

    completeShape() {
        if (this.points.length < 3) {
            alert('Please add at least 3 points to create a shape');
            return;
        }

        // Remove existing polyline
        if (this.polyline) {
            this.map.removeLayer(this.polyline);
        }

        // Create closed polygon
        if (this.polygon) {
            this.map.removeLayer(this.polygon);
        }
        this.polygon = L.polygon(this.points, {
            color: '#276EF1',
            weight: 3,
            fillColor: '#276EF1',
            fillOpacity: 0.2
        }).addTo(this.map);

        // Calculate and display area and perimeter
        const area = this.calculateArea();
        const perimeter = this.calculatePerimeter();

        document.getElementById('area').textContent = area.toFixed(2);
        document.getElementById('length').textContent = perimeter.toFixed(2);
        document.querySelector('.perimeter-info').style.display = 'block';

        // Fit map to show entire polygon
        this.map.fitBounds(this.polygon.getBounds());
    }

    clearPoints() {
        // Remove all markers
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];

        // Remove polyline and polygon
        if (this.polyline) this.map.removeLayer(this.polyline);
        if (this.polygon) this.map.removeLayer(this.polygon);

        // Clear points array
        this.points = [];

        // Reset UI
        document.getElementById('completeShape').disabled = true;
        document.querySelector('.perimeter-info').style.display = 'none';
        document.getElementById('pointCount').textContent = '0';
    }

    calculateArea() {
        if (!this.polygon) return 0;
        return L.GeometryUtil.geodesicArea(this.polygon.getLatLngs()[0]) / 1000000; // Convert to sq km
    }

    calculatePerimeter() {
        if (!this.polygon) return 0;
        let length = 0;
        const points = this.polygon.getLatLngs()[0];
        
        for (let i = 0; i < points.length; i++) {
            const j = (i + 1) % points.length;
            length += points[i].distanceTo(points[j]);
        }
        
        return length / 1000; // Convert to km
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const perimeterManager = new PerimeterManager();
}); 