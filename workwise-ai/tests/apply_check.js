const http = require('http');

function req(method, path, formData, cookies) {
  return new Promise((resolve, reject) => {
    let body = '';
    if (formData) {
      body = Object.keys(formData).map(k =>
        encodeURIComponent(k) + '=' + encodeURIComponent(formData[k])
      ).join('&');
    }
    const opts = {
      method,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    };
    if (cookies) opts.headers.Cookie = cookies;
    if (body) opts.headers['Content-Length'] = Buffer.byteLength(body);

    const r = http.request({ host: '127.0.0.1', port: 5000, path, ...opts }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({
        status: res.statusCode,
        body: d,
        setCookie: res.headers['set-cookie'],
        location: res.headers.location,
      }));
    });
    r.on('error', reject);
    if (body) r.write(body);
    r.end();
  });
}

function extractCookie(setCookie) {
  if (!setCookie) return '';
  const arr = Array.isArray(setCookie) ? setCookie : [setCookie];
  return arr.map(c => c.split(';')[0]).join('; ');
}

(async () => {
  // 1. Login as demo user
  const login = await req('POST', '/login', {
    email: 'demo@workwise.ai', password: 'demo1234',
  });
  const cookie = extractCookie(login.setCookie);
  console.log('login status:', login.status, '| cookie:', cookie ? 'yes' : 'NO');

  // 2. GET the apply page for job 1
  const apply = await req('GET', '/job/1/apply', null, cookie);
  console.log('apply page status:', apply.status);

  // Check for Jinja errors / traceback in output
  if (apply.body.includes('Traceback') || apply.body.includes('Error')) {
    console.log('!!! ERROR FOUND IN APPLY PAGE OUTPUT');
    const idx = apply.body.indexOf('Traceback') >= 0 ? apply.body.indexOf('Traceback') : apply.body.indexOf('Error');
    console.log(apply.body.slice(Math.max(0, idx - 100), idx + 500));
  } else {
    console.log('apply page rendered without server error');
  }

  // Check required element IDs for the inline script
  const ids = ['apply-form','apply-errors','apply-success','success-job',
    'email','phone','tenth_percent','twelfth_percent','cgpa','summary',
    'projects','certificates'];
  const missing = ids.filter(id => !apply.body.includes('id="' + id + '"'));
  console.log('Missing element IDs in apply page:', missing.length ? missing : 'NONE');

  // Check the inline script rendered jobId/jobTitle correctly
  const jobIdMatch = apply.body.match(/const jobId = (\d+);/);
  const jobTitleMatch = apply.body.match(/const jobTitle = (".*?");/);
  console.log('rendered jobId:', jobIdMatch ? jobIdMatch[1] : 'NOT FOUND');
  console.log('rendered jobTitle:', jobTitleMatch ? jobTitleMatch[1] : 'NOT FOUND');
})();
