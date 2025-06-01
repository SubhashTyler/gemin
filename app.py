import React, { useState, useEffect, useRef, useCallback } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, getDoc, addDoc, setDoc, updateDoc, deleteDoc, onSnapshot, collection, query, where, getDocs } from 'firebase/firestore';

// Global variables provided by the Canvas environment
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : {};
const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? initialAuthToken : null; // Corrected variable name

// Initialize Firebase outside the component to prevent re-initialization
let app;
let db;
let auth;

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  auth = getAuth(app);
  console.log("Firebase initialized successfully.");
} catch (error) {
  console.error("Firebase initialization error:", error);
  // Handle error, e.g., display a message to the user
}

// Utility function to generate a simple UUID
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

// Main App Component
const App = () => {
  const [currentView, setCurrentView] = useState('home'); // 'home', 'busSearch', 'seatSelection', 'bookingConfirmation', 'trackBus', 'routes', 'dashboard'
  const [buses, setBuses] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [busLocations, setBusLocations] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [bookingDetails, setBookingDetails] = useState(null);
  const [userBookings, setUserBookings] = useState([]); // New state for user bookings
  const [searchCriteria, setSearchCriteria] = useState({ from: '', to: '', date: '' });
  const [passengerDetails, setPassengerDetails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userId, setUserId] = useState(null);
  const [isAuthReady, setIsAuthReady] = useState(false);

  // Refs for map simulation
  const mapCanvasRef = useRef(null);
  const busPositionRef = useRef({ x: 0, y: 0, index: 0 });
  const animationFrameId = useRef(null);

  // Firebase Authentication and Data Initialization
  useEffect(() => {
    const setupFirebase = async () => {
      try {
        if (initialAuthToken) {
          console.log("Attempting sign-in with custom token...");
          await signInWithCustomToken(auth, initialAuthToken);
        } else {
          console.log("Attempting anonymous sign-in...");
          await signInAnonymously(auth);
        }
      } catch (e) {
        console.error("Firebase Auth Error during setup:", e);
        setError("Failed to authenticate. Some features might not work.");
      }
    };

    const unsubscribeAuth = onAuthStateChanged(auth, (user) => {
      if (user) {
        setUserId(user.uid);
        setIsAuthReady(true);
        console.log("User authenticated. UID:", user.uid);
      } else {
        setUserId(null);
        setIsAuthReady(true); // Still ready, but user is anonymous or not signed in
        console.log("User not authenticated (anonymous or signed out).");
      }
    });

    if (!isAuthReady) {
      setupFirebase();
    }

    return () => unsubscribeAuth();
  }, [isAuthReady]);

  // Fetch initial data and set up real-time listeners
  useEffect(() => {
    if (!isAuthReady || !db) {
      console.log("Firebase not ready or DB not initialized. Skipping data fetch.");
      return;
    }

    setLoading(true);
    console.log("Attempting to fetch initial data...");

    // Fetch and listen for buses
    const busesCollectionRef = collection(db, `artifacts/${appId}/public/data/buses`);
    const unsubscribeBuses = onSnapshot(busesCollectionRef, (snapshot) => {
      const fetchedBuses = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setBuses(fetchedBuses);
      setLoading(false);
      console.log("Buses fetched:", fetchedBuses.length);
    }, (err) => {
      console.error("Error fetching buses:", err);
      setError("Failed to load bus data. Check Firebase permissions.");
      setLoading(false);
    });

    // Fetch and listen for routes
    const routesCollectionRef = collection(db, `artifacts/${appId}/public/data/routes`);
    const unsubscribeRoutes = onSnapshot(routesCollectionRef, (snapshot) => {
      const fetchedRoutes = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setRoutes(fetchedRoutes);
      console.log("Routes fetched:", fetchedRoutes.length);
    }, (err) => {
      console.error("Error fetching routes:", err);
      setError("Failed to load route data. Check Firebase permissions.");
    });

    // Fetch and listen for bus locations (simulated real-time)
    const busLocationsCollectionRef = collection(db, `artifacts/${appId}/public/data/bus_locations`);
    const unsubscribeBusLocations = onSnapshot(busLocationsCollectionRef, (snapshot) => {
      const fetchedLocations = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setBusLocations(fetchedLocations);
      console.log("Bus locations fetched:", fetchedLocations.length);
    }, (err) => {
      console.error("Error fetching bus locations:", err);
      setError("Failed to load bus location data. Check Firebase permissions.");
    });

    // Initial data population (only if collections are empty)
    const populateInitialData = async () => {
      try {
        const busDocs = await getDocs(busesCollectionRef);
        if (busDocs.empty) {
          console.log("Populating initial bus data...");
          await addDoc(busesCollectionRef, {
            operator: 'Swift Travels', type: 'AC Seater', capacity: 40, routeId: 'route-001',
            departureTime: '08:00 AM', arrivalTime: '01:00 PM', basePrice: 750, origin: 'Delhi', destination: 'Jaipur',
            stops: ['Gurgaon', 'Manesar', 'Behror', 'Shahpura']
          });
          await addDoc(busesCollectionRef, {
            operator: 'Royal Express', type: 'Non-AC Sleeper', capacity: 30, routeId: 'route-002',
            departureTime: '10:00 AM', arrivalTime: '04:00 PM', basePrice: 900, origin: 'Delhi', destination: 'Agra',
            stops: ['Mathura', 'Vrindavan']
          });
          await addDoc(busesCollectionRef, {
            operator: 'Green Line', type: 'AC Sleeper', capacity: 35, routeId: 'route-003',
            departureTime: '09:30 AM', arrivalTime: '03:30 PM', basePrice: 1200, origin: 'Jaipur', destination: 'Udaipur',
            stops: ['Ajmer', 'Bhilwara']
          });
          console.log("Initial bus data populated.");
        }

        const routeDocs = await getDocs(routesCollectionRef);
        if (routeDocs.empty) {
          console.log("Populating initial route data...");
          await addDoc(routesCollectionRef, {
            id: 'route-001', name: 'Delhi to Jaipur', origin: 'Delhi', destination: 'Jaipur',
            stoppages: ['Gurgaon', 'Manesar', 'Behror', 'Shahpura', 'Jaipur'],
            coordinates: [
              { lat: 28.6139, lon: 77.2090 }, { lat: 28.4595, lon: 77.0266 }, { lat: 28.3375, lon: 76.9388 },
              { lat: 27.9157, lon: 76.2890 }, { lat: 27.4646, lon: 75.9555 }, { lat: 26.9124, lon: 75.7873 }
            ]
          });
          await addDoc(routesCollectionRef, {
            id: 'route-002', name: 'Delhi to Agra', origin: 'Delhi', destination: 'Agra',
            stoppages: ['Delhi', 'Mathura', 'Vrindavan', 'Agra'],
            coordinates: [
              { lat: 28.6139, lon: 77.2090 }, { lat: 27.4924, lon: 77.6737 },
              { lat: 27.5700, lon: 77.6500 }, { lat: 27.1767, lon: 78.0078 }
            ]
          });
          await addDoc(routesCollectionRef, {
            id: 'route-003', name: 'Jaipur to Udaipur', origin: 'Jaipur', destination: 'Udaipur',
            stoppages: ['Jaipur', 'Ajmer', 'Bhilwara', 'Udaipur'],
            coordinates: [
              { lat: 26.9124, lon: 75.7873 }, { lat: 26.4499, lon: 74.6399 },
              { lat: 25.3468, lon: 74.6358 }, { lat: 24.5854, lon: 73.7125 }
            ]
          });
          console.log("Initial route data populated.");
        }

        const busLocationsDocs = await getDocs(busLocationsCollectionRef);
        if (busLocationsDocs.empty) {
          console.log("Populating initial bus location data...");
          await setDoc(doc(busLocationsCollectionRef, 'bus-001'), {
            busId: 'bus-001', lat: 28.6139, lon: 77.2090, timestamp: Date.now(), routeId: 'route-001', currentStopIndex: 0
          });
          await setDoc(doc(busLocationsCollectionRef, 'bus-002'), {
            busId: 'bus-002', lat: 28.6139, lon: 77.2090, timestamp: Date.now(), routeId: 'route-002', currentStopIndex: 0
          });
          console.log("Initial bus location data populated.");
        }
      } catch (e) {
        console.error("Error populating initial data:", e);
        setError("Failed to populate initial data. Check Firebase permissions.");
      }
    };

    if (isAuthReady) {
      populateInitialData();
    }

    return () => {
      unsubscribeBuses();
      unsubscribeRoutes();
      unsubscribeBusLocations();
    };
  }, [isAuthReady, userId]); // Depend on isAuthReady and userId

  // Fetch user-specific bookings
  useEffect(() => {
    if (!isAuthReady || !db || !userId) {
      console.log("Firebase not ready, DB not initialized, or userId not available. Skipping user bookings fetch.");
      return;
    }

    console.log("Attempting to fetch user bookings for userId:", userId);
    const bookingsCollectionRef = collection(db, `artifacts/${appId}/users/${userId}/bookings`);
    const unsubscribeBookings = onSnapshot(bookingsCollectionRef, (snapshot) => {
      const fetchedBookings = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
      setUserBookings(fetchedBookings);
      console.log("User bookings fetched:", fetchedBookings.length);
    }, (err) => {
      console.error("Error fetching user bookings:", err);
      setError("Failed to load your bookings. Check Firebase permissions.");
    });

    return () => unsubscribeBookings();
  }, [isAuthReady, userId]);


  // Simulate bus movement
  useEffect(() => {
    if (!isAuthReady || busLocations.length === 0 || routes.length === 0) {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
        animationFrameId.current = null;
      }
      return;
    }

    const simulateMovement = () => {
      busLocations.forEach(async (busLoc) => {
        const route = routes.find(r => r.id === busLoc.routeId);
        if (!route || !route.coordinates || route.coordinates.length === 0) return;

        let nextStopIndex = (busLoc.currentStopIndex || 0) + 1;
        if (nextStopIndex >= route.coordinates.length) {
          nextStopIndex = 0; // Loop back to start
        }

        const currentCoord = route.coordinates[busLoc.currentStopIndex || 0];
        const nextCoord = route.coordinates[nextStopIndex];

        // Simple linear interpolation for smooth movement
        const steps = 100; // Number of steps between two coordinates
        const currentStep = (busLoc.step || 0) + 1;

        let newLat, newLon;
        if (currentStep <= steps) {
          newLat = currentCoord.lat + (nextCoord.lat - currentCoord.lat) * (currentStep / steps);
          newLon = currentCoord.lon + (nextCoord.lon - currentCoord.lon) * (currentStep / steps);
        } else {
          newLat = nextCoord.lat;
          newLon = nextCoord.lon;
          nextStopIndex = (busLoc.currentStopIndex || 0) + 1;
          if (nextStopIndex >= route.coordinates.length) {
            nextStopIndex = 0; // Loop back to start
          }
          busLoc.currentStopIndex = nextStopIndex;
          busLoc.step = 0;
        }

        try {
          await updateDoc(doc(db, `artifacts/${appId}/public/data/bus_locations`, busLoc.id), {
            lat: newLat,
            lon: newLon,
            timestamp: Date.now(),
            currentStopIndex: currentStep > steps ? nextStopIndex : (busLoc.currentStopIndex || 0),
            step: currentStep > steps ? 0 : currentStep
          });
        } catch (e) {
          console.error("Error updating bus location:", e);
        }
      });
    };

    const interval = setInterval(simulateMovement, 1000); // Update every 1 second

    return () => clearInterval(interval);
  }, [isAuthReady, busLocations, routes]);


  const handleSearch = (e) => {
    e.preventDefault();
    setCurrentView('busSearch');
  };

  const handleSelectBus = (bus) => {
    setSelectedBus(bus);
    setSelectedSeats([]); // Clear previous selection
    setPassengerDetails({});
    setCurrentView('seatSelection');
  };

  const toggleSeatSelection = (seatNumber) => {
    if (selectedSeats.includes(seatNumber)) {
      setSelectedSeats(selectedSeats.filter(seat => seat !== seatNumber));
      setPassengerDetails(prev => {
        const newDetails = { ...prev };
        delete newDetails[seatNumber];
        return newDetails;
      });
    } else {
      setSelectedSeats([...selectedSeats, seatNumber]);
      setPassengerDetails(prev => ({
        ...prev,
        [seatNumber]: { name: '', gender: '', age: '' }
      }));
    }
  };

  const handlePassengerDetailChange = (seatNumber, field, value) => {
    setPassengerDetails(prev => ({
      ...prev,
      [seatNumber]: {
        ...prev[seatNumber],
        [field]: value
      }
    }));
  };

  const handleBookSeats = async () => {
    if (selectedSeats.length === 0 || !selectedBus) {
      setError("Please select seats and a bus first.");
      return;
    }

    const passengers = selectedSeats.map(seatNumber => ({
      seatNumber,
      ...passengerDetails[seatNumber]
    }));

    const bookingId = generateUUID();
    const totalFare = selectedSeats.length * selectedBus.basePrice;

    const bookingData = {
      bookingId,
      busId: selectedBus.id,
      routeId: selectedBus.routeId,
      date: searchCriteria.date,
      passengers,
      totalFare,
      status: 'Confirmed',
      timestamp: Date.now(),
      userId: userId // Store userId for private data
    };

    try {
      if (!userId) {
        setError("User not authenticated. Please wait or refresh.");
        return;
      }
      await addDoc(collection(db, `artifacts/${appId}/users/${userId}/bookings`), bookingData);
      setBookingDetails(bookingData);
      setCurrentView('dashboard'); // Redirect to dashboard after booking
      setError(null);
    } catch (e) {
      console.error("Error booking seats:", e);
      setError("Failed to book seats. Please try again. Check Firebase permissions for user bookings.");
    }
  };

  // Map drawing function
  const drawMap = useCallback(() => {
    const canvas = mapCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height); // Clear canvas

    // Draw background
    ctx.fillStyle = '#ADD8E6'; // Light blue for sky/water
    ctx.fillRect(0, 0, width, height);
    ctx.fillStyle = '#8B4513'; // Brown for ground
    ctx.fillRect(0, height * 0.7, width, height * 0.3);

    // Draw a simple road
    ctx.strokeStyle = '#555';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.moveTo(0, height * 0.75);
    ctx.lineTo(width, height * 0.75);
    ctx.stroke();

    // Draw road markings
    ctx.strokeStyle = '#FFF';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(0, height * 0.75);
    ctx.lineTo(width, height * 0.75);
    ctx.stroke();
    ctx.setLineDash([]); // Reset line dash

    // Draw simple houses/buildings
    ctx.fillStyle = '#A9A9A9'; // Dark gray
    ctx.fillRect(50, height * 0.6 - 30, 40, 30);
    ctx.fillRect(150, height * 0.6 - 50, 60, 50);
    ctx.fillRect(250, height * 0.6 - 40, 50, 40);

    // Draw trees
    ctx.fillStyle = '#228B22'; // Forest green
    ctx.beginPath();
    ctx.arc(70, height * 0.6 - 35, 15, 0, Math.PI * 2);
    ctx.arc(180, height * 0.6 - 55, 20, 0, Math.PI * 2);
    ctx.arc(280, height * 0.6 - 45, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#8B4513'; // Brown for trunk
    ctx.fillRect(68, height * 0.6 - 20, 4, 20);
    ctx.fillRect(178, height * 0.6 - 35, 4, 30);
    ctx.fillRect(278, height * 0.6 - 25, 4, 25);

    // Draw simulated bus
    const busX = busPositionRef.current.x;
    const busY = busPositionRef.current.y;

    ctx.fillStyle = '#FF0000'; // Red bus
    ctx.fillRect(busX - 15, busY - 10, 30, 20); // Bus body
    ctx.fillStyle = '#000';
    ctx.fillRect(busX - 10, busY + 5, 5, 5); // Wheel 1
    ctx.fillRect(busX + 5, busY + 5, 5, 5); // Wheel 2
    ctx.fillStyle = '#FFF';
    ctx.fillRect(busX - 8, busY - 5, 16, 8); // Window

    // Draw current location text
    ctx.fillStyle = '#000';
    ctx.font = '14px Inter, sans-serif';
    ctx.fillText(`Bus Location: ${busPositionRef.current.location || 'Unknown'}`, 10, 20);
  }, []);

  // Animate bus position on canvas
  useEffect(() => {
    if (currentView !== 'trackBus' || busLocations.length === 0 || routes.length === 0) {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
        animationFrameId.current = null;
      }
      return;
    }

    const busToTrack = busLocations[0]; // Assuming we track the first bus for simplicity
    const route = routes.find(r => r.id === busToTrack.routeId);
    if (!route || !route.coordinates || route.coordinates.length < 2) return;

    const canvas = mapCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    const width = canvas.width;
    const height = canvas.height;

    // Scale coordinates to canvas size
    const minLat = Math.min(...route.coordinates.map(c => c.lat));
    const maxLat = Math.max(...route.coordinates.map(c => c.lat));
    const minLon = Math.min(...route.coordinates.map(c => c.lon));
    const maxLon = Math.max(...route.coordinates.map(c => c.lon));

    const scaleX = (lon) => (lon - minLon) / (maxLon - minLon) * width * 0.8 + width * 0.1;
    const scaleY = (lat) => height * 0.8 - (lat - minLat) / (maxLat - minLat) * height * 0.6; // Invert Y for canvas

    const animateBus = () => {
      const currentLoc = busLocations.find(loc => loc.id === busToTrack.id);
      if (!currentLoc) return;

      const x = scaleX(currentLoc.lon);
      const y = scaleY(currentLoc.lat);

      busPositionRef.current = {
        x,
        y: height * 0.75, // Keep bus on the road line for simple visual
        location: `Lat: ${currentLoc.lat.toFixed(4)}, Lon: ${currentLoc.lon.toFixed(4)}`
      };

      drawMap();
      animationFrameId.current = requestAnimationFrame(animateBus);
    };

    animateBus();

    return () => {
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [currentView, busLocations, routes, drawMap]);

  // QR Code drawing function
  const drawQRCode = useCallback((canvas, text) => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = canvas.width;

    ctx.clearRect(0, 0, size, size);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, size, size);

    // Simple pattern for QR code - this is not a real QR code algorithm
    // In a real application, you would use a QR code library.
    const blockSize = size / 20; // Divide into 20x20 blocks
    for (let i = 0; i < 20; i++) {
      for (let j = 0; j < 20; j++) {
        if ((i + j) % 3 === 0) { // Simple pattern
          ctx.fillStyle = '#000000';
          ctx.fillRect(i * blockSize, j * blockSize, blockSize, blockSize);
        }
      }
    }

    ctx.fillStyle = '#000000';
    ctx.font = '10px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Scan for Details', size / 2, size - 10);
  }, []);

  // UseEffect to draw QR code when booking details are available and view is bookingConfirmation
  useEffect(() => {
    if (currentView === 'bookingConfirmation' && bookingDetails) {
      const qrCanvas = document.getElementById('qrCanvas');
      if (qrCanvas) {
        const qrText = JSON.stringify({
          bookingId: bookingDetails.bookingId,
          busId: bookingDetails.busId,
          date: bookingDetails.date,
          passengers: bookingDetails.passengers.map(p => ({ name: p.name, seat: p.seatNumber })),
          totalFare: bookingDetails.totalFare
        });
        drawQRCode(qrCanvas, qrText);
      }
    }
  }, [currentView, bookingDetails, drawQRCode]);


  // Filtered buses based on search criteria
  const filteredBuses = buses.filter(bus => {
    return (
      (!searchCriteria.from || bus.origin.toLowerCase().includes(searchCriteria.from.toLowerCase())) &&
      (!searchCriteria.to || bus.destination.toLowerCase().includes(searchCriteria.to.toLowerCase()))
      // Date filtering can be added here if bus data includes dates, or simulated
    );
  });

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen bg-gray-100 text-gray-700">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 font-inter text-gray-800">
      {/* Header */}
      <header className="bg-white shadow-md py-4 px-6 flex justify-between items-center rounded-b-lg">
        <h1 className="text-3xl font-bold text-blue-600">BusLink</h1>
        <nav>
          <ul className="flex space-x-6">
            <li><button onClick={() => setCurrentView('home')} className="text-lg font-medium text-gray-700 hover:text-blue-500 transition duration-300">Home</button></li>
            <li><button onClick={() => setCurrentView('trackBus')} className="text-lg font-medium text-gray-700 hover:text-blue-500 transition duration-300">Track Bus</button></li>
            <li><button onClick={() => setCurrentView('routes')} className="text-lg font-medium text-gray-700 hover:text-blue-500 transition duration-300">Routes</button></li>
            <li><button onClick={() => setCurrentView('dashboard')} className="text-lg font-medium text-gray-700 hover:text-blue-500 transition duration-300">My Bookings</button></li> {/* New button */}
            {userId && <li className="text-sm text-gray-500">User ID: {userId}</li>}
          </ul>
        </nav>
      </header>

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mx-auto mt-4 w-11/12 md:w-3/4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {/* Home View */}
      {currentView === 'home' && (
        <div className="flex flex-col items-center justify-center p-8">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-lg mt-10">
            <h2 className="text-3xl font-extrabold text-center text-blue-700 mb-8">Find Your Bus</h2>
            <form onSubmit={handleSearch} className="space-y-6">
              <div>
                <label htmlFor="from" className="block text-sm font-medium text-gray-700 mb-2">From</label>
                <input
                  type="text"
                  id="from"
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={searchCriteria.from}
                  onChange={(e) => setSearchCriteria({ ...searchCriteria, from: e.target.value })}
                  placeholder="e.g., Delhi"
                  required
                />
              </div>
              <div>
                <label htmlFor="to" className="block text-sm font-medium text-gray-700 mb-2">To</label>
                <input
                  type="text"
                  id="to"
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={searchCriteria.to}
                  onChange={(e) => setSearchCriteria({ ...searchCriteria, to: e.target.value })}
                  placeholder="e.g., Jaipur"
                  required
                />
              </div>
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">Date of Journey</label>
                <input
                  type="date"
                  id="date"
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  value={searchCriteria.date}
                  onChange={(e) => setSearchCriteria({ ...searchCriteria, date: e.target.value })}
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-300"
              >
                Search Buses
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Bus Search Results View */}
      {currentView === 'busSearch' && (
        <div className="p-8">
          <h2 className="text-3xl font-bold text-center text-blue-700 mb-8">Available Buses</h2>
          {filteredBuses.length === 0 ? (
            <p className="text-center text-gray-600">No buses found for your search criteria. Please try different options.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredBuses.map(bus => (
                <div key={bus.id} className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition duration-300">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{bus.operator} - {bus.type}</h3>
                  <p className="text-gray-600">Route: {bus.origin} to {bus.destination}</p>
                  <p className="text-gray-600">Departure: {bus.departureTime} | Arrival: {bus.arrivalTime}</p>
                  <p className="text-green-600 font-bold mt-2">Available Seats: {bus.capacity - (
                    // This is a simplified availability. In a real app, you'd fetch actual booked seats for this bus/date.
                    Math.floor(Math.random() * (bus.capacity / 2)) // Simulate some booked seats
                  )}</p>
                  <p className="text-2xl font-extrabold text-blue-600 mt-4">₹{bus.basePrice}</p>
                  <button
                    onClick={() => handleSelectBus(bus)}
                    className="mt-6 w-full py-3 px-4 rounded-md shadow-md text-lg font-semibold text-white bg-blue-500 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-400 transition duration-300"
                  >
                    View Seats
                  </button>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => setCurrentView('home')}
            className="mt-8 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300"
          >
            &larr; Back to Search
          </button>
        </div>
      )}

      {/* Seat Selection View */}
      {currentView === 'seatSelection' && selectedBus && (
        <div className="p-8">
          <h2 className="text-3xl font-bold text-center text-blue-700 mb-8">Select Your Seats for {selectedBus.operator}</h2>
          <div className="bg-white p-6 rounded-xl shadow-lg max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
              <div>
                <p className="text-xl font-semibold text-gray-900">{selectedBus.origin} to {selectedBus.destination}</p>
                <p className="text-gray-600">{selectedBus.departureTime} - {selectedBus.arrivalTime}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-medium text-gray-700">Total Selected: <span className="font-bold text-blue-600">{selectedSeats.length}</span></p>
                <p className="text-2xl font-extrabold text-green-600">Total Fare: ₹{selectedSeats.length * selectedBus.basePrice}</p>
              </div>
            </div>

            {/* Seat Layout */}
            <div className="grid grid-cols-5 gap-4 p-4 border border-gray-300 rounded-lg bg-gray-50 mb-8">
              {Array.from({ length: selectedBus.capacity }).map((_, index) => {
                const seatNumber = index + 1;
                const isBooked = Math.random() < 0.2; // Simulate 20% of seats as booked
                const isSelected = selectedSeats.includes(seatNumber);

                let seatColorClass = 'bg-green-400 hover:bg-green-500'; // Available
                let cursorStyle = 'cursor-pointer';
                if (isBooked) {
                  seatColorClass = 'bg-red-400'; // Booked
                  cursorStyle = 'cursor-not-allowed';
                } else if (isSelected) {
                  seatColorClass = 'bg-blue-400 hover:bg-blue-500'; // Selected
                }

                return (
                  <button
                    key={seatNumber}
                    className={`relative w-16 h-16 flex items-center justify-center text-white font-bold rounded-md shadow-md transition duration-200 ease-in-out ${seatColorClass} ${cursorStyle}`}
                    onClick={() => !isBooked && toggleSeatSelection(seatNumber)}
                    disabled={isBooked}
                  >
                    {seatNumber}
                    {isBooked && <span className="absolute top-1 right-1 text-xs">X</span>}
                  </button>
                );
              })}
            </div>

            {/* Legend */}
            <div className="flex justify-center space-x-6 mb-8">
              <div className="flex items-center">
                <span className="w-4 h-4 bg-green-400 rounded-full mr-2"></span> Available
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-blue-400 rounded-full mr-2"></span> Selected
              </div>
              <div className="flex items-center">
                <span className="w-4 h-4 bg-red-400 rounded-full mr-2"></span> Booked
              </div>
            </div>

            {/* Passenger Details Form */}
            {selectedSeats.length > 0 && (
              <div className="mt-8 bg-gray-50 p-6 rounded-xl shadow-inner">
                <h3 className="text-2xl font-bold text-blue-700 mb-6">Passenger Details</h3>
                {selectedSeats.map(seatNumber => (
                  <div key={seatNumber} className="mb-6 p-4 border border-gray-200 rounded-md bg-white shadow-sm">
                    <h4 className="text-lg font-semibold text-gray-800 mb-3">Seat {seatNumber}</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label htmlFor={`name-${seatNumber}`} className="block text-sm font-medium text-gray-700">Name</label>
                        <input
                          type="text"
                          id={`name-${seatNumber}`}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          value={passengerDetails[seatNumber]?.name || ''}
                          onChange={(e) => handlePassengerDetailChange(seatNumber, 'name', e.target.value)}
                          required
                        />
                      </div>
                      <div>
                        <label htmlFor={`gender-${seatNumber}`} className="block text-sm font-medium text-gray-700">Gender</label>
                        <select
                          id={`gender-${seatNumber}`}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          value={passengerDetails[seatNumber]?.gender || ''}
                          onChange={(e) => handlePassengerDetailChange(seatNumber, 'gender', e.target.value)}
                          required
                        >
                          <option value="">Select</option>
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor={`age-${seatNumber}`} className="block text-sm font-medium text-gray-700">Age</label>
                        <input
                          type="number"
                          id={`age-${seatNumber}`}
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          value={passengerDetails[seatNumber]?.age || ''}
                          onChange={(e) => handlePassengerDetailChange(seatNumber, 'age', e.target.value)}
                          min="1"
                          max="100"
                          required
                        />
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  onClick={handleBookSeats}
                  className="mt-6 w-full py-3 px-4 rounded-md shadow-md text-lg font-semibold text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition duration-300"
                >
                  Book Selected Seats
                </button>
              </div>
            )}
          </div>
          <button
            onClick={() => setCurrentView('busSearch')}
            className="mt-8 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300"
          >
            &larr; Back to Buses
          </button>
        </div>
      )}

      {/* Booking Confirmation View (now less critical as dashboard is primary view) */}
      {currentView === 'bookingConfirmation' && bookingDetails && (
        <div className="p-8 flex flex-col items-center">
          <div className="bg-white p-8 rounded-xl shadow-2xl w-full max-w-2xl text-center">
            <h2 className="text-4xl font-extrabold text-green-600 mb-6">Booking Confirmed!</h2>
            <p className="text-lg text-gray-700 mb-4">Your journey is all set. Here are your details:</p>

            <div className="border border-gray-200 rounded-lg p-6 mb-6 text-left">
              <p className="text-xl font-semibold mb-2">Booking ID: <span className="text-blue-600">{bookingDetails.bookingId}</span></p>
              <p className="text-md text-gray-700">Bus: {buses.find(b => b.id === bookingDetails.busId)?.operator} - {buses.find(b => b.id === bookingDetails.busId)?.type}</p>
              <p className="text-md text-gray-700">Route: {buses.find(b => b.id === bookingDetails.busId)?.origin} to {buses.find(b => b.id === bookingDetails.busId)?.destination}</p>
              <p className="text-md text-gray-700">Date: {bookingDetails.date}</p>
              <p className="text-md text-gray-700">Departure: {buses.find(b => b.id === bookingDetails.busId)?.departureTime}</p>
              <p className="text-md text-gray-700 font-bold mt-3">Passengers & Seats:</p>
              <ul className="list-disc list-inside ml-4 text-gray-700">
                {bookingDetails.passengers.map((p, index) => (
                  <li key={index}>{p.name} ({p.gender}, {p.age}) - Seat {p.seatNumber}</li>
                ))}
              </ul>
              <p className="text-2xl font-extrabold text-green-700 mt-4">Total Fare: ₹{bookingDetails.totalFare}</p>
            </div>

            <div className="flex flex-col items-center mb-6">
              <h3 className="text-2xl font-bold text-blue-700 mb-4">Your E-Ticket QR Code</h3>
              <canvas id="qrCanvas" width="200" height="200" className="border border-gray-300 rounded-lg shadow-md"></canvas>
              <p className="text-sm text-gray-500 mt-2">Show this QR code to the bus conductor.</p>
            </div>

            <button
              onClick={() => setCurrentView('dashboard')} // Go to dashboard instead of home
              className="mt-6 py-3 px-6 rounded-md shadow-md text-lg font-semibold text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-300"
            >
              Go to My Bookings
            </button>
          </div>
        </div>
      )}

      {/* Track Bus View */}
      {currentView === 'trackBus' && (
        <div className="p-8 flex flex-col items-center">
          <h2 className="text-3xl font-bold text-center text-blue-700 mb-8">Real-time Bus Tracking</h2>
          <div className="bg-white p-6 rounded-xl shadow-lg w-full max-w-3xl">
            <p className="text-gray-700 mb-4 text-center">
              Tracking Bus: {busLocations.length > 0 && busLocations[0].busId ? busLocations[0].busId : 'N/A'}
              <br/>
              Current Location: {busPositionRef.current.location || 'Simulating...'}
            </p>
            <canvas
              ref={mapCanvasRef}
              width="600"
              height="300"
              className="border border-gray-300 rounded-lg shadow-md w-full max-w-full h-auto"
              style={{ display: 'block', margin: '0 auto' }}
            ></canvas>
            <p className="text-sm text-gray-500 mt-4 text-center">
              (This is a simulated map for demonstration purposes. In a real application, a full-fledged mapping API like Google Maps would be integrated.)
            </p>
          </div>
          <button
            onClick={() => setCurrentView('home')}
            className="mt-8 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300"
          >
            &larr; Back to Home
          </button>
        </div>
      )}

      {/* Routes View */}
      {currentView === 'routes' && (
        <div className="p-8">
          <h2 className="text-3xl font-bold text-center text-blue-700 mb-8">Our Bus Routes</h2>
          {routes.length === 0 ? (
            <p className="text-center text-gray-600">No routes defined yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {routes.map(route => (
                <div key={route.id} className="bg-white p-6 rounded-xl shadow-lg">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{route.name}</h3>
                  <p className="text-gray-600">Origin: {route.origin}</p>
                  <p className="text-gray-600">Destination: {route.destination}</p>
                  <p className="text-gray-700 font-medium mt-3">Stoppages:</p>
                  <ul className="list-disc list-inside ml-4 text-gray-600">
                    {route.stoppages.map((stop, i) => (
                      <li key={i}>{stop}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={() => setCurrentView('home')}
            className="mt-8 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300"
          >
            &larr; Back to Home
          </button>
        </div>
      )}

      {/* Dashboard View (My Bookings) */}
      {currentView === 'dashboard' && (
        <div className="p-8">
          <h2 className="text-3xl font-bold text-center text-blue-700 mb-8">My Bookings</h2>
          {userBookings.length === 0 ? (
            <p className="text-center text-gray-600">You have no bookings yet. Go to Home to book a bus!</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {userBookings.map(booking => {
                const bookedBus = buses.find(bus => bus.id === booking.busId);
                return (
                  <div key={booking.id} className="bg-white p-6 rounded-xl shadow-lg">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Booking ID: {booking.bookingId}</h3>
                    <p className="text-gray-600">Status: <span className="font-bold text-green-600">{booking.status}</span></p>
                    {bookedBus && (
                      <>
                        <p className="text-gray-600">Bus: {bookedBus.operator} - {bookedBus.type}</p>
                        <p className="text-gray-600">Route: {bookedBus.origin} to {bookedBus.destination}</p>
                        <p className="text-gray-600">Departure: {bookedBus.departureTime} on {booking.date}</p>
                      </>
                    )}
                    <p className="text-gray-700 font-medium mt-3">Passengers:</p>
                    <ul className="list-disc list-inside ml-4 text-gray-600">
                      {booking.passengers.map((p, index) => (
                        <li key={index}>{p.name} (Seat {p.seatNumber})</li>
                      ))}
                    </ul>
                    <p className="text-2xl font-extrabold text-blue-600 mt-4">Total Fare: ₹{booking.totalFare}</p>
                    {/* Optional: Add a button to view QR code or full details again */}
                    {/* <button className="mt-4 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300">View QR</button> */}
                  </div>
                );
              })}
            </div>
          )}
          <button
            onClick={() => setCurrentView('home')}
            className="mt-8 py-2 px-4 rounded-md text-blue-600 border border-blue-600 hover:bg-blue-50 transition duration-300"
          >
            &larr; Back to Home
          </button>
        </div>
      )}
    </div>
  );
};

export default App;
