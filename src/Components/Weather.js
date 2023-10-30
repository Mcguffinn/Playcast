import React, { useEffect } from "react";

const Weather = () => {
  const success = (userPosition) => {
    const locationData = userPosition.coords;

    console.log("Your current position is:");
    console.log(`Latitude : ${locationData.latitude}`);
    console.log(`Longitude: ${locationData.longitude}`);
    console.log(`More or less ${locationData.accuracy} meters.`);
  };

  useEffect(() => {
    const options = {
      enableHighAccuracy: true,
      timeout: 5000,
      maximumAge: 0,
    };
    async function get_user_location() {
      try {
        if (navigator.geolocation) {
          navigator.permissions
            .query({ name: "geolocation" })
            .then((result) => {
              if (result.state === "granted") {
                console.log(result.state);
                return navigator.geolocation.getCurrentPosition(success);
              } else if (result.state === "prompt") {
                console.log(result.state);
                return navigator.geolocation.getCurrentPosition(
                  success,
                  options
                );
              } else if (result.state === "denied") {
              }
            });
        }
      } catch (error) {
        console.log(error);
      }
    }
    get_user_location();
  }, []);

  return <section></section>;
};

export default Weather();
