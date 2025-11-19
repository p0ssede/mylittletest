import { useEffect, useState } from "react";

export default function Chat({ token, userId }) {
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [ws, setWs] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/users")
      .then(res => res.json())
      .then(setUsers);

    const socket = new WebSocket("ws://127.0.0.1:8000/ws");
    socket.onopen = () => socket.send(token);
    socket.onmessage = e => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, { sender: data.sender, text: data.text }]);
    };
    setWs(socket);

    return () => socket.close();
  }, []);

  const selectUser = async (user) => {
    setSelectedUser(user);
    const res = await fetch(`http://127.0.0.1:8000/messages/${user.id}?token=${token}`);
    const msgs = await res.json();
    setMessages(msgs);
  };

  const sendMessage = () => {
    if (!selectedUser) return;
    ws.send(JSON.stringify({ receiver: selectedUser.id, text: input }));
    setMessages(prev => [...prev, { sender: userId, text: input }]);
    setInput("");
  };

  return (
    <div style={{ display: "flex" }}>
      <div style={{ width: "200px", borderRight: "1px solid black" }}>
        <h3>Users</h3>
        {users.map(u => (
          <div key={u.id} onClick={() => selectUser(u)} style={{ cursor: "pointer", margin: "5px" }}>
            {u.username}
          </div>
        ))}
      </div>
      <div style={{ flex: 1, padding: "10px" }}>
        <h3>Chat {selectedUser ? `with ${selectedUser.username}` : ""}</h3>
        <div style={{ height: "300px", overflowY: "auto", border: "1px solid gray", padding: "5px" }}>
          {messages.map((m, i) => (
            <div key={i} style={{ textAlign: m.sender === userId ? "right" : "left" }}>
              <b>{m.sender === userId ? "You" : selectedUser?.username}:</b> {m.text}
            </div>
          ))}
        </div>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Message..." />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
