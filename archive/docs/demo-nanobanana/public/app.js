const form = document.getElementById('gen-form');
const promptEl = document.getElementById('prompt');
const modelEl = document.getElementById('model');
const statusEl = document.getElementById('status');
const imgEl = document.getElementById('output');
const downloadEl = document.getElementById('download');

function setStatus(t) {
  statusEl.textContent = t || '';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const prompt = promptEl.value.trim();
  const model = modelEl.value;
  if (!prompt) {
    setStatus('请填写提示词');
    return;
  }
  imgEl.removeAttribute('src');
  downloadEl.removeAttribute('href');
  setStatus('正在生成...');
  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      setStatus('生成失败');
      return;
    }
    const data = await resp.json();
    if (data.imageBase64) {
      const b = atob(data.imageBase64);
      const bytes = new Uint8Array(b.length);
      for (let i = 0; i < b.length; i++) bytes[i] = b.charCodeAt(i);
      const blob = new Blob([bytes], { type: data.mimeType || 'image/png' });
      const url = URL.createObjectURL(blob);
      imgEl.src = url;
      downloadEl.href = url;
      setStatus('生成完成');
    } else if (data.message) {
      setStatus(data.message);
    } else {
      setStatus('未返回图片');
    }
  } catch (err) {
    setStatus('网络错误');
  }
});
