const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3001;

app.get('/env.js', (req, res) => {
  res.setHeader('Content-Type', 'application/javascript');
  res.send(`window.ENV = { API_BASE: "${process.env.API_BASE || 'http://localhost:8000'}" };`);
});

app.use(express.static(path.join(__dirname, 'public')));
app.get('*', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));
app.listen(PORT, '0.0.0.0', () => console.log(`Frontend: http://localhost:${PORT}`));
