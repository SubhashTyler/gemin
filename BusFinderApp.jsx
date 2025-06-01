import { useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export default function BusFinderApp() {
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [date, setDate] = useState(new Date());
  const [bookings, setBookings] = useState([]);

  const handleSearch = () => {
    const dummyBooking = { from, to, date: date.toDateString(), bus: "Express Bus 101" };
    setBookings([dummyBooking]);
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <Tabs defaultValue="home" className="w-full">
        <TabsList className="grid grid-cols-4 gap-2 mb-4">
          <TabsTrigger value="home">Home</TabsTrigger>
          <TabsTrigger value="track">Track Bus</TabsTrigger>
          <TabsTrigger value="routes">Routes</TabsTrigger>
          <TabsTrigger value="bookings">My Booking</TabsTrigger>
        </TabsList>

        <TabsContent value="home">
          <Card>
            <CardContent className="p-4 space-y-4">
              <h2 className="text-xl font-semibold">Find Your Bus</h2>
              <Input placeholder="From" value={from} onChange={e => setFrom(e.target.value)} />
              <Input placeholder="To" value={to} onChange={e => setTo(e.target.value)} />
              <Calendar mode="single" selected={date} onSelect={setDate} />
              <Button onClick={handleSearch}>Search Bus</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="track">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold">Track Your Bus</h2>
              <p>Feature coming soon with real-time tracking.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="routes">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold">Available Routes</h2>
              <ul className="list-disc list-inside">
                <li>City A - City B</li>
                <li>City C - City D</li>
                <li>City E - City F</li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bookings">
          <Card>
            <CardContent className="p-4 space-y-2">
              <h2 className="text-xl font-semibold">My Bookings</h2>
              {bookings.length === 0 ? (
                <p>No bookings found.</p>
              ) : (
                bookings.map((b, index) => (
                  <div key={index} className="border p-2 rounded-md">
                    <p>From: {b.from}</p>
                    <p>To: {b.to}</p>
                    <p>Date: {b.date}</p>
                    <p>Bus: {b.bus}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 
