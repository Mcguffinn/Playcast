// Function to get the user's location from browser
function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                // Success callback
                function(position) {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    
                    console.log(`Browser location obtained: ${latitude}, ${longitude}`);
                    
                    // Store the coordinates in localStorage for future use
                    localStorage.setItem('userLatitude', latitude);
                    localStorage.setItem('userLongitude', longitude);
                    
                    resolve({
                        latitude: latitude,
                        longitude: longitude
                    });
                },
                // Error callback
                function(error) {
                    console.error("Error getting location:", error);
                    reject(error);
                },
                // Options
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                }
            );
        } else {
            reject(new Error("Geolocation is not supported by this browser"));
        }
    });
}

// Add location parameters to URL
function addLocationToUrl(url) {
    const lat = localStorage.getItem('userLatitude');
    const lng = localStorage.getItem('userLongitude');
    
    if (lat && lng) {
        // Check if URL already has parameters
        const hasParams = url.includes('?');
        const separator = hasParams ? '&' : '?';
        
        // Add coordinates as query parameters
        return `${url}${separator}lat=${lat}&lng=${lng}`;
    }
    
    return url;
}

// Update links when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Try to get location immediately
    getUserLocation()
        .then(coords => {
            console.log('Location retrieved successfully');
            
            // Update all Playcast links with the location
            const playcasterLinks = document.querySelectorAll('a[href="/playcast"]');
            playcasterLinks.forEach(link => {
                link.href = addLocationToUrl(link.href);
            });
        })
        .catch(error => {
            console.error('Failed to get location:', error);
            // We'll fall back to IP-based location in this case
        });
});