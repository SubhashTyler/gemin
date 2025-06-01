# Simulated Bus Finder App in Python (CLI-based)
import datetime

class BusFinderApp:
    def __init__(self):
        self.routes = [
            {"from": "City A", "to": "City B", "bus": "Express 101", "departure": "09:00", "arrival": "12:00"},
            {"from": "City C", "to": "City D", "bus": "Rapid 202", "departure": "14:00", "arrival": "18:00"},
            {"from": "City E", "to": "City F", "bus": "Deluxe 303", "departure": "07:00", "arrival": "11:00"},
        ]
        self.bookings = []

    def show_menu(self):
        print("\nWelcome to Bus Finder App")
        print("1. Find Bus")
        print("2. Track Bus")
        print("3. Show Routes")
        print("4. My Bookings")
        print("5. Exit")

    def find_bus(self):
        from_city = input("Enter starting city: ")
        to_city = input("Enter destination city: ")
        date_str = input("Enter date (YYYY-MM-DD): ")

        try:
            travel_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date format.")
            return

        found = False
        for route in self.routes:
            if route["from"].lower() == from_city.lower() and route["to"].lower() == to_city.lower():
                found = True
                print(f"\nBus Found: {route['bus']} | Departure: {route['departure']} | Arrival: {route['arrival']}")
                book = input("Do you want to book this bus? (y/n): ").lower()
                if book == 'y':
                    self.bookings.append({
                        "from": from_city,
                        "to": to_city,
                        "date": travel_date,
                        "bus": route['bus']
                    })
                    print("Booking confirmed!")
        if not found:
            print("No buses found for the selected route.")

    def track_bus(self):
        bus_name = input("Enter the bus name to track: ")
        print(f"Tracking {bus_name}... (simulated)\nEstimated location: 50% of route covered")

    def show_routes(self):
        print("\nAvailable Routes:")
        for route in self.routes:
            print(f"{route['from']} -> {route['to']} | Bus: {route['bus']} | Departure: {route['departure']} | Arrival: {route['arrival']}")

    def show_bookings(self):
        if not self.bookings:
            print("\nNo bookings found.")
            return
        print("\nMy Bookings:")
        for booking in self.bookings:
            print(f"From: {booking['from']} | To: {booking['to']} | Date: {booking['date']} | Bus: {booking['bus']}")

    def run(self):
        while True:
            self.show_menu()
            choice = input("Select an option (1-5): ")
            if choice == '1':
                self.find_bus()
            elif choice == '2':
                self.track_bus()
            elif choice == '3':
                self.show_routes()
            elif choice == '4':
                self.show_bookings()
            elif choice == '5':
                print("Exiting Bus Finder App. Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    app = BusFinderApp()
    app.run()
