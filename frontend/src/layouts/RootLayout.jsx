import { useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "../components/Header.jsx";
import Footer from "../components/Footer.jsx";
import { useMedicineSearch } from "../hooks/useMedicineSearch.js";

export const API_URL = "http://127.0.0.1:8000";

// Search state (and recent-search history) is lifted here, above the
// router's Outlet, so Home and Search share the exact same handleSearch
// call and in-flight state instead of each page owning its own copy.
export default function RootLayout() {
  const [dbCount, setDbCount] = useState(0);
  const search = useMedicineSearch(API_URL);

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      <Header dbCount={dbCount} setDbCount={setDbCount} apiUrl={API_URL} />
      <div className="flex-1">
        <Outlet context={{ apiUrl: API_URL, ...search }} />
      </div>
      <Footer />
    </div>
  );
}
