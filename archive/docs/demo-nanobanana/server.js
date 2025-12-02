const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 3000;

function send(res, status, body, headers) {
  const hdrs = Object.assign({}, headers || {}, { 'Content-Length': Buffer.byteLength(body) });
  res.writeHead(status, hdrs);
  res.end(body);
}

function serveStatic(req, res) {
  const u = new URL(req.url, `http://${req.headers.host}`);
  let pathname = u.pathname;
  if (pathname === '/') pathname = '/index.html';
  const filePath = path.join(__dirname, 'public', pathname.replace(/^\//, ''));
  fs.stat(filePath, (err, stat) => {
    if (err || !stat.isFile()) {
      send(res, 404, 'Not Found', { 'Content-Type': 'text/plain' });
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const types = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.svg': 'image/svg+xml'
    };
    const contentType = types[ext] || 'application/octet-stream';
    fs.createReadStream(filePath).on('error', () => {
      send(res, 500, 'Server Error', { 'Content-Type': 'text/plain' });
    }).pipe(res);
    res.setHeader('Content-Type', contentType);
  });
}

async function handleGenerate(req, res) {
  const chunks = [];
  req.on('data', (c) => chunks.push(c));
  req.on('end', async () => {
    try {
      const body = JSON.parse(Buffer.concat(chunks).toString('utf-8'));
      const prompt = String(body.prompt || '').trim();
      const model = String(body.model || 'gemini-3-pro-image-preview');
      if (!prompt) {
        send(res, 400, JSON.stringify({ error: '缺少提示词' }), { 'Content-Type': 'application/json' });
        return;
      }
      const apiKey = process.env.GEMINI_API_KEY;
      if (!apiKey) {
        send(res, 500, JSON.stringify({ error: '服务器未配置 GEMINI_API_KEY' }), { 'Content-Type': 'application/json' });
        return;
      }
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;
      const reqBody = {
        contents: [
          {
            parts: [
              { text: prompt }
            ]
          }
        ]
      };
      let resp;
      try {
        resp = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'x-goog-api-key': apiKey,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(reqBody)
        });
      } catch (e) {
        send(res, 502, JSON.stringify({ error: '无法连接到生成服务' }), { 'Content-Type': 'application/json' });
        return;
      }
      if (!resp.ok) {
        const txt = await resp.text();
        send(res, resp.status, JSON.stringify({ error: '生成失败', detail: txt }), { 'Content-Type': 'application/json' });
        return;
      }
      const data = await resp.json();
      const candidates = data.candidates || [];
      let imagePart = null;
      if (candidates.length > 0 && candidates[0].content && Array.isArray(candidates[0].content.parts)) {
        for (const p of candidates[0].content.parts) {
          const inlineCamel = p.inlineData && p.inlineData.data ? p.inlineData : null;
          const inlineSnake = p.inline_data && p.inline_data.data ? p.inline_data : null;
          imagePart = inlineCamel || inlineSnake;
          if (imagePart) break;
        }
      }
      if (!imagePart) {
        send(res, 200, JSON.stringify({ message: '未返回图片', raw: data }), { 'Content-Type': 'application/json' });
        return;
      }
      const mime = imagePart.mimeType || imagePart.mime_type || 'image/png';
      send(res, 200, JSON.stringify({ imageBase64: imagePart.data, mimeType: mime }), { 'Content-Type': 'application/json' });
    } catch (err) {
      send(res, 400, JSON.stringify({ error: '请求体错误' }), { 'Content-Type': 'application/json' });
    }
  });
}

const server = http.createServer((req, res) => {
  const u = new URL(req.url, `http://${req.headers.host}`);
  if (req.method === 'POST' && u.pathname === '/api/generate') {
    handleGenerate(req, res);
    return;
  }
  if (req.method === 'GET') {
    serveStatic(req, res);
    return;
  }
  send(res, 405, 'Method Not Allowed', { 'Content-Type': 'text/plain' });
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});
