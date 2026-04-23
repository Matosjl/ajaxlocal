import "@/App.css";
import "./responsive.css";
import "highlight.js/styles/github-dark.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AjaxChat from "./pages/AjaxChat";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AjaxChat />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </div>
  );
}

export default App;
