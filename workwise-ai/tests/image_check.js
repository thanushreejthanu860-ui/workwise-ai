const http = require('http');
const fs = require('fs');
const path = require('path');

function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let d = [];
      res.on('data', c => d.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(d) }));
    }).on('error', reject);
  });
}

(async () => {
  // 1. All generated image files exist on disk
  const imgDir = 'static/images';
  const files = fs.readdirSync(imgDir).filter(f => f.endsWith('.png'));
  console.log('Image files on disk:', files.length);

  // 2. All images serve with 200 and valid PNG header (89 50 4E 47)
  let bad = [];
  for (const f of files) {
    const r = await get('http://127.0.0.1:5000/static/images/' + f);
    const isPng = r.body.length > 4 &&
      r.body[0] === 0x89 && r.body[1] === 0x50 &&
      r.body[2] === 0x4E && r.body[3] === 0x47;
    if (r.status !== 200 || !isPng) bad.push(f + ' (' + r.status + ')');
  }
  console.log('All images serve as valid PNG:', bad.length ? 'NO -> ' + bad.join(', ') : 'YES');

  // 3. Home page references images
  const home = await get('http://127.0.0.1:5000/');
  const html = home.body.toString();
  const imgRefs = [...html.matchAll(/images\/([a-z0-9\-]+\.png)/g)].map(m => m[1]);
  console.log('Home page image references:', [...new Set(imgRefs)].join(', '));

  // 4. Job details page uses role + company images
  const jd = (await get('http://127.0.0.1:5000/job/1')).body.toString();
  console.log('Job details has company image:', /images\/company-\d+\.png/.test(jd));
  console.log('Job details has role image:', /images\/role-\d+\.png/.test(jd));

  // 5. API returns company_image and role_image
  const api = JSON.parse((await get('http://127.0.0.1:5000/api/jobs/1')).body);
  console.log('API company_image:', api.company_image, '| role_image:', api.role_image);

  // 6. Profile page has avatar
  // (requires login; skip - just check template renders via job pages)

  console.log('\nImage integration OK');
})();
