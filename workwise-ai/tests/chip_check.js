const http = require('http');
function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d }));
    }).on('error', reject);
  });
}
(async () => {
  // 1. Home page chips now use real filter params
  const home = await get('http://127.0.0.1:5000/');
  const chipHrefs = [...home.body.matchAll(/class="chip"[^>]*href="([^"]*)"/g)].map(m => m[1]);
  console.log('Home chips:');
  chipHrefs.forEach(h => console.log('  ', h));

  // 2. Each chip target should return a valid jobs page (200)
  console.log('\nChip target status:');
  for (const h of chipHrefs) {
    const r = await get('http://127.0.0.1:5000' + h);
    console.log('  ', h, '->', r.status);
  }

  // 3. Verify the API honours each chip filter
  console.log('\nAPI filter results:');
  const tests = [
    '/api/jobs?work_mode=Remote',
    '/api/jobs?category=Analytics',
    '/api/jobs?experience=fresher',
    '/api/jobs?type=internship',
    '/api/jobs?q=Startup',
  ];
  for (const t of tests) {
    const r = await get('http://127.0.0.1:5000' + t);
    const d = JSON.parse(r.body);
    console.log('  ', t, '->', d.count, 'jobs');
  }
})();
