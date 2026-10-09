const http = require('http');

function postForm(path, formData) {
  return new Promise((resolve, reject) => {
    const body = Object.keys(formData).map(k =>
      encodeURIComponent(k) + '=' + encodeURIComponent(formData[k])).join('&');
    const r = http.request({
      host: '127.0.0.1', port: 5000, path, method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Content-Length': Buffer.byteLength(body),
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({
        status: res.statusCode, body: d, setCookie: res.headers['set-cookie'],
      }));
    });
    r.on('error', reject);
    r.write(body);
    r.end();
  });
}

function getPage(path, cookie) {
  return new Promise((resolve, reject) => {
    http.get({ host: '127.0.0.1', port: 5000, path, headers: { Cookie: cookie } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d }));
    }).on('error', reject);
  });
}

function cookieFrom(sc) {
  if (!sc) return '';
  const arr = Array.isArray(sc) ? sc : [sc];
  return arr.map(c => c.split(';')[0]).join('; ');
}

(async () => {
  const login = await postForm('/login', { email: 'demo@workwise.ai', password: 'demo1234' });
  const cookie = cookieFrom(login.setCookie);

  const pages = ['/dashboard', '/profile', '/resume', '/job/1', '/job/1/apply', '/fair-wage', '/roadmaps', '/interview-prep'];
  for (const p of pages) {
    const r = await getPage(p, cookie);
    const imgCount = (r.body.match(/images\/[a-z0-9\-]+\.png/g) || []).length;
    const hasError = r.body.includes('Traceback') || r.body.includes('Internal Server Error');
    console.log(p, '->', r.status, '| images:', imgCount, hasError ? '| ERROR!' : '');
  }
})();
