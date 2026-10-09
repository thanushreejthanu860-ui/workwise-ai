const http = require('http');
function get(url, cookies) {
  return new Promise((resolve, reject) => {
    const opts = { headers: cookies ? { Cookie: cookies } : {} };
    http.get(url, opts, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d, headers: res.headers }));
    }).on('error', reject);
  });
}
(async () => {
  // Check if .modal and .chat-window CSS use display:flex (which overrides hidden attr)
  const css = await get('http://127.0.0.1:5000/static/css/style.css');
  const modalRule = css.body.match(/\.modal\s*\{[^}]*\}/);
  const chatRule = css.body.match(/\.chat-window\s*\{[^}]*\}/);
  const bannerRule = css.body.match(/\.notif-banner\s*\{[^}]*\}/);
  console.log('.modal has display:flex:', modalRule && modalRule[0].includes('display: flex'));
  console.log('.chat-window has display:flex:', chatRule && chatRule[0].includes('display: flex'));
  console.log('.notif-banner has display:flex:', bannerRule && bannerRule[0].includes('display: flex'));
  console.log('Global [hidden] rule exists:', /\[hidden\]\s*\{[^}]*display:\s*none/.test(css.body));
})();
