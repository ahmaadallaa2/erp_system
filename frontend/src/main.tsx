import React from "react";
import ReactDOM from "react-dom/client";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 3000,
        style: {
          background: "#0f172a",
          color: "#ffffff",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "12px",
          padding: "12px 14px",
          fontSize: "14px",
        },
        success: {
          style: {
            border: "1px solid rgba(0, 229, 255, 0.25)",
          },
          iconTheme: {
            primary: "#00e5ff",
            secondary: "#0f172a",
          },
        },
        error: {
          style: {
            border: "1px solid rgba(255, 77, 77, 0.25)",
          },
          iconTheme: {
            primary: "#ff6b6b",
            secondary: "#0f172a",
          },
        },
      }}
    />
  </React.StrictMode>
);
