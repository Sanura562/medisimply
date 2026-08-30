import { Route, Routes } from "react-router-dom";
import RootLayout from "./layouts/RootLayout.jsx";
import HomePage from "./pages/HomePage.jsx";
import SearchPage from "./pages/SearchPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchPage />} />
      </Route>
    </Routes>
  );
}
