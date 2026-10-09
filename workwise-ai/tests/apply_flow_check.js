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

function postJSON(path, data, cookie) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const r = http.request({
      host: '127.0.0.1', port: 5000, path, method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...(cookie ? { Cookie: cookie } : {}),
      },
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d, setCookie: res.headers['set-cookie'] }));
    });
    r.on('error', reject);
    r.write(body);
    r.end();
  });
}

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
      res.on('end', () => resolve({ status: res.statusCode, body: d, setCookie: res.headers['set-cookie'] }));
    });
    r.on('error', reject);
    r.write(body);
    r.end();
  });
}

function cookieFrom(setCookie) {
  if (!setCookie) return '';
  const arr = Array.isArray(setCookie) ? setCookie : [setCookie];
  return arr.map(c => c.split(';')[0]).join('; ');
}

(async () => {
  // 1. CSS [hidden] fix is served
  const css = await get('http://127.0.0.1:5000/static/css/style.css');
  console.log('CSS [hidden]{display:none!important} served:',
    /\[hidden\]\s*\{[^}]*display:\s*none\s*!important/.test(css.body));

  // 2. Login
  const login = await postForm('/login', { email: 'demo@workwise.ai', password: 'demo1234' });
  const cookie = cookieFrom(login.setCookie);
  console.log('login:', login.status, '| cookie:', cookie ? 'yes' : 'NO');

  // 3. Apply to job 4 (not yet applied by demo user)
  const apply = await postJSON('/api/jobs/4/apply', {
    email: 'demo@workwise.ai', phone: '9876543210',
    tenth_percent: '88%', twelfth_percent: '82%', cgpa: '8.1',
    summary: 'I am passionate about software development and building useful tools.',
    projects: 'Sales Dashboard — Power BI', certificates: 'Python for Data Science',
  }, cookie);
  console.log('apply to job 4:', apply.status, '|', apply.body);

  // 4. Verify it appears in dashboard
  const dash = await get('http://127.0.0.1:5000/api/dashboard');
  // note: this GET has no cookie, so it will be 401; use postJSON-like with cookie instead
  const dash2 = await new Promise((resolve, reject) => {
    http.get({ host: '127.0.0.1', port: 5000, path: '/api/dashboard', headers: { Cookie: cookie } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ status: res.statusCode, body: d }));
    }).on('error', reject);
  });
  const dd = JSON.parse(dash2.body);
  console.log('dashboard total_applications:', dd.total_applications);

  // 5. Duplicate apply should be 409
  const dup = await postJSON('/api/jobs/4/apply', {
    email: 'demo@workwise.ai', phone: '9876543210',
    tenth_percent: '88%', twelfth_percent: '82%', cgpa: '8.1',
    summary: 'I am passionate about software development and building useful tools.',
  }, cookie);
  console.log('duplicate apply:', dup.status, '(expect 409)');
})();
