import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./stil.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

/* Ana ekrana eklenince çevrimdışı da açılsın diye servis çalışanı */
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  });
}
