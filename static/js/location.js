// Function to get the user's location from browser
function getUserLocation() {
    return new Promise((resolve, reject) => {
        console.log('Attempting to get location...');
        // Check if we already have fresh location data (less than 30 minutes old)
        const storedLat = localStorage.getItem('userLatitude');
        const storedLng = localStorage.getItem('userLongitude');
        const timestamp = localStorage.getItem('locationTimestamp');
        const currentTime = Date.now();
        
        // If we have recent location data (within the last 30 minutes), use it
        if (storedLat && storedLng && timestamp && 
            (currentTime - timestamp < 30 * 60 * 1000)) {
            console.log(`Using stored location: ${storedLat}, ${storedLng}`);
            
            // Update the server in the background
            updateServerWithLocation(storedLat, storedLng);
            
            resolve({
                latitude: storedLat,
                longitude: storedLng
            });
            return;
        }
        
        // Otherwise, get fresh location data
        if (navigator.geolocation) {
            console.log('Requesting browser geolocation...');
            navigator.geolocation.getCurrentPosition(
                // Success callback
                function(position) {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    
                    console.log(`Browser location obtained: ${latitude}, ${longitude}`);
                    
                    // Store the coordinates in localStorage with timestamp
                    localStorage.setItem('userLatitude', latitude);
                    localStorage.setItem('userLongitude', longitude);
                    localStorage.setItem('locationTimestamp', Date.now());
                    
                    // Also update the server immediately
                    updateServerWithLocation(latitude, longitude);
                    
                    resolve({
                        latitude: latitude,
                        longitude: longitude
                    });
                },
                // Error callback
                function(error) {
                    console.error("Geolocation error:", error);
                    
                    // Show visual feedback instead of silent fail
                    const prompt = document.getElementById('location-prompt');
                    prompt.style.display = 'block';
                    
                    // Add click handler for manual retry
                    document.getElementById('grant-location').addEventListener('click', () => {
                        prompt.style.display = 'none';
                        getUserLocation().then(resolve).catch(reject);
                    });
    
                    // Add dismiss handler
                    document.getElementById('dismiss-prompt').addEventListener('click', () => {
                        prompt.style.display = 'none';
                        reject(error);
                    });
                },
                // Options
                {
                    enableHighAccuracy: true,
                    timeout: 15000, // 10 second timeout
                    maximumAge: 0
                }
            );
        } else {
            reject(new Error("Geolocation is not supported by this browser"));
        }
    });
}

function updatePlaycastButton() {
    const playcastBtn = document.getElementById('playcastBtn');
    if (playcastBtn) {
        // Don't set loading state here - do it only when actually requesting location
        
        playcastBtn.addEventListener('click', function(e) {
            e.preventDefault();
            // Show loading state
            this.innerHTML = '<div class="button"><span class="spinner-border spinner-border-sm"></span> Locating...</div>';
            
            // Set a timeout to restore the button if getting location takes too long
            const buttonTimeout = setTimeout(() => {
                this.innerHTML = '<div class="button">Get a Playcast</div>';
            }, 10000);
            
            // Try to get location
            getUserLocation()
                .then(coords => {
                    clearTimeout(buttonTimeout);
                    window.location.href = `/playcast?lat=${coords.latitude}&lng=${coords.longitude}`;
                })
                .catch(error => {
                    clearTimeout(buttonTimeout);
                    console.error('Failed to get location:', error);
                    this.innerHTML = '<div class="button">Get a Playcast</div>';
                    // Still navigate, but let server handle fallback
                    window.location.href = '/playcast';
                });
        });
    }
}

// Get location in background without blocking
function updateLocationInBackground() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                
                console.log(`Background location update: ${latitude}, ${longitude}`);
                
                // Store the coordinates in localStorage with timestamp
                localStorage.setItem('userLatitude', latitude);
                localStorage.setItem('userLongitude', longitude);
                localStorage.setItem('locationTimestamp', Date.now());
                
                // Update server with new location
                updateServerWithLocation(latitude, longitude);
            },
            // Error callback - silent fail for background updates
            function(error) {
                console.error("Background location update failed:", error);
            },
            // Options
            {
                enableHighAccuracy: false, // Lower accuracy is fine for background
                timeout: 5000, // Shorter timeout for background
                maximumAge: 0
            }
        );
    }
}

// Update server with current location
function updateServerWithLocation(latitude, longitude) {
    // Ensure we have valid coordinates
    if (!latitude || !longitude) {
        console.warn('Invalid coordinates, skipping server update');
        return;
    }

    // Make sure we're using the full URL path (important on some deployments)
    const base = window.location.origin;
    const url = `${base}/api/weather?lat=${latitude}&lng=${longitude}`;
    console.log(`Attempting to update server with location: ${url}`);

    // Add timeout and error handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);

    fetch(url, {
        signal: controller.signal,
        method: 'GET',
        credentials: 'same-origin', // Important for cookies/session
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            console.warn(`Server returned status: ${response.status}`);
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Successfully updated server with location');
        // Store the city and region for fallback
        if (data.city && data.region) {
            localStorage.setItem('lastKnownCity', data.city);
            localStorage.setItem('lastKnownRegion', data.region);
        }
        updatePageWithLocationData(data);
    })
    .catch(error => {
        console.error('Server update failed:', error);
        // Use fallback data from localStorage
        updatePageWithLocationData({
            city: localStorage.getItem('lastKnownCity') || 'Unknown',
            region: localStorage.getItem('lastKnownRegion') || 'Unknown'
        });
    })
    .finally(() => {
        clearTimeout(timeoutId);
    });
}

// Update any location-dependent elements on the page
function updatePageWithLocationData(data) {
    // Update location display if it exists
    const locationHeading = document.querySelector('.display-6.text-center');
    if (locationHeading && data.city && data.region) {
        locationHeading.textContent = `Location: ${data.city}, ${data.region}`;
    }
    
    // Update weather info if present on the page
    const weatherStatus = document.querySelector('.display-3.title:last-of-type');
    if (weatherStatus && data.weatherStatus) {
        weatherStatus.textContent = data.weatherStatus;
    }
    
    const temperatureDisplay = document.querySelector('.display-3.title:nth-of-type(2)');
    if (temperatureDisplay && data.temperature) {
        temperatureDisplay.textContent = `${data.temperature}°F`;
    }
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

// Update all links to include location parameters
function updateAllLinks() {
    // Update all links with location information
    const allLinks = document.querySelectorAll('a[href]');
    allLinks.forEach(link => {
        // Only modify internal links
        if (link.href.startsWith(window.location.origin)) {
            link.href = addLocationToUrl(link.href);
        }
    });
}

// Update forms to include location data
function updateForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Get coordinates
            const lat = localStorage.getItem('userLatitude');
            const lng = localStorage.getItem('userLongitude');
            
            if (lat && lng) {
                // Create hidden input fields for lat/lng if they don't exist
                if (!form.querySelector('input[name="lat"]')) {
                    const latInput = document.createElement('input');
                    latInput.type = 'hidden';
                    latInput.name = 'lat';
                    latInput.value = lat;
                    form.appendChild(latInput);
                }
                
                if (!form.querySelector('input[name="lng"]')) {
                    const lngInput = document.createElement('input');
                    lngInput.type = 'hidden';
                    lngInput.name = 'lng';
                    lngInput.value = lng;
                    form.appendChild(lngInput);
                }
            }
        });
    });
}

// Make API requests include location parameters
function updateFetchRequests() {
    // Store the original fetch function
    const originalFetch = window.fetch;
    
    // Override fetch to add location parameters to URLs
    window.fetch = function(url, options) {
        // Only modify internal URLs that don't already have location params
        if (typeof url === 'string' && 
            url.startsWith(window.location.origin) && 
            !url.includes('lat=') && 
            !url.includes('lng=')) {
            
            url = addLocationToUrl(url);
        }
        
        // Call the original fetch with our modified URL
        return originalFetch.call(this, url, options);
    };
}

// Periodically refresh location in the background
function setupLocationRefresh() {
    // Refresh location every 30 minutes
    setInterval(() => {
        updateLocationInBackground();
    }, 30 * 60 * 1000); // 30 minutes
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, requesting geolocation');
    
    // Force a geolocation prompt by calling this function directly
    requestGeolocation();
    
    // Set up the rest of the page
    updatePlaycastButton();
    updateForms();
    updateAllLinks();
    setupLocationRefresh();

    // Update play buttons to include location info when clicked
    document.querySelectorAll('.play-button').forEach(button => {
        button.addEventListener('click', function() {
            const playlistId = this.getAttribute('data-playlist-id');
            const lat = localStorage.getItem('userLatitude');
            const lng = localStorage.getItem('userLongitude');
            
            if (lat && lng) {
                // Include location when playing playlist
                fetch(`${window.location.origin}/play-playlist/${playlistId}?lat=${lat}&lng=${lng}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Reload the page to show the embedded player
                            window.location.href = addLocationToUrl(window.location.href);
                        } else {
                            alert('Could not play playlist: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error playing playlist:', error);
                        alert('An error occurred while trying to play the playlist');
                    });
            } else {
                // Fallback if no location available
                fetch(`${window.location.origin}/play-playlist/${playlistId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            window.location.reload();
                        } else {
                            alert('Could not play playlist: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error playing playlist:', error);
                        alert('An error occurred while trying to play the playlist');
                    });
            }
            
            // Prevent default action
            return false;
        });
    });
});

function requestGeolocation() {
    if (navigator.geolocation) {
        console.log('Explicitly requesting geolocation permission');
        
        // Show loading state immediately
        const playcastBtn = document.getElementById('playcastBtn');
        if (playcastBtn) {
            playcastBtn.innerHTML = '<div class="button"><span class="spinner-border spinner-border-sm"></span> Locating...</div>';
        }

        // Ensure there's a timeout handler that restores the button
        const locationTimeout = setTimeout(() => {
            console.log('Geolocation timed out, restoring button state');
            if (playcastBtn) {
                playcastBtn.innerHTML = '<div class="button">Get a Playcast</div>';
            }
            // Use the fallback method
            fallbackToIpLocation();
        }, 16000); // Slightly longer than the geolocation timeout

        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                clearTimeout(locationTimeout); // Clear the timeout
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                
                console.log(`Geolocation granted: ${latitude}, ${longitude}`);
                
                // Store the coordinates in localStorage
                localStorage.setItem('userLatitude', latitude);
                localStorage.setItem('userLongitude', longitude);
                localStorage.setItem('locationTimestamp', Date.now());
                
                // Update the server with the new location
                updateServerWithLocation(latitude, longitude);
                
                // Restore button state
                if (playcastBtn) {
                    playcastBtn.innerHTML = '<div class="button">Get a Playcast</div>';
                }
            },
            // Error callback
            function(error) {
                clearTimeout(locationTimeout); // Clear the timeout
                console.error("Geolocation permission denied or error:", error);
                // Restore button state
                if (playcastBtn) {
                    playcastBtn.innerHTML = '<div class="button">Get a Playcast</div>';
                }
                
                fallbackToIpLocation();
            },
            // Options
            {
                enableHighAccuracy: false, // Set to false for faster results
                timeout: 15000,
                maximumAge: 60000 // Allow cached positions up to 1 minute old
            }
        );
    } else {
        console.error("Geolocation not supported by this browser");
        fallbackToIpLocation();
    }
           
}

function fallbackToIpLocation() {
    console.log('Falling back to IP geolocation');
    fetch(`${window.location.origin}/api/ip-location`)
        .then(response => response.json())
        .then(data => {
            console.log('Fallback to IP location successful:', data);
            if (data.city && data.region) {
                localStorage.setItem('lastKnownCity', data.city);
                localStorage.setItem('lastKnownRegion', data.region);
                updatePageWithLocationData(data);
            }
            
            // Extract coordinates from the 'loc' property
            if (data.loc && data.loc.includes(',')) {
                const [lat, lng] = data.loc.split(',');
                localStorage.setItem('userLatitude', lat);
                localStorage.setItem('userLongitude', lng);
                localStorage.setItem('locationTimestamp', Date.now());
            }
        })
        .catch(err => console.error('IP location fallback failed:', err));
}