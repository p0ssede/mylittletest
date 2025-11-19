import { useState } from "react";

export default function Login({ setToken, setUserId }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  const handleLogin = async () => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    const res = await fetch("http://127.0.0.1:8000/login", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      setToken(data.access_token);
      setUserId(data.user_id);
    } else {
      setMsg("Invalid login");
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <button onClick={handleLogin}>Login</button>
      <p>{msg}</p>
    </div>
  );
}
