import { useState } from "react";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";

export default function App() {
  const [token, setToken] = useState(null);
  const [userId, setUserId] = useState(null);

  if (!token) {
    return (
      <div>
        <h1>Mini Social Network</h1>
        <Register />
        <Login setToken={setToken} setUserId={setUserId} />
      </div>
    );
  }

  return <Chat token={token} userId={userId} />;
}
