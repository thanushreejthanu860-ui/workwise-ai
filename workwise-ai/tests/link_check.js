const http = require('http');

function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d, headers: res.headers }));
    }).on('error', reject);
  });
}

const BASE = 'http://127.0.0.1:5000';
const pages = ['/', '/login', '/register', '/jobs', '/job/1', '/fair-wage',
  '/roadmaps', '/interview-prep', '/404-test'];

(async () => {
  const seen = new Set();
  const broken = [];
  for (const p of pages) {
    const r = await get(BASE + p);
    if (r.status >= 400 && p !== '/404-test') {
      broken.push(p + ' -> ' + r.status);
      continue;
    }
    // extract internal links
    const links = [...r.body.matchAll(/href="(\/[^"]*)"/g)].map(m => m[1]);
    for (const link of links) {
      const clean = link.split('?')[0].split('#')[0];
      if (seen.has(clean) || !clean.startsWith('/')) continue;
      seen.add(clean);
      // skip API-style and static
      if (clean.startsWith('/api/') || clean.startsWith('/static/')) continue;
      const lr = await get(BASE + clean);
      // a page link should be 200, or 302 redirect to login (protected)
      if (lr.status >= 400) {
        broken.push(clean + ' (from ' + p + ') -> ' + lr.status);
      }
    }
  }
  console.log('Checked', seen.size, 'unique internal links.');
  if (broken.length) {
    console.log('BROKEN LINKS:');
    broken.forEach(b => console.log('  ', b));
  } else {
    console.log('No broken internal links found.');
  }
})();
