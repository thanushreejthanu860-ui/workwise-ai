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
  // 1. Check all element IDs jobs.js needs exist in rendered /jobs
  const page = await get('http://127.0.0.1:5000/jobs');
  const ids = ['job-filters','f-q','f-location','f-experience','f-job-type',
    'f-work-mode','f-category','f-min-salary','f-max-salary','clear-filters',
    'sort','tab-jobs','tab-internships','jobs-title','job-grid','jobs-status',
    'job-modal','modal-title','modal-close','modal-body'];
  const missing = ids.filter(id => !page.body.includes('id="' + id + '"'));
  console.log('Missing element IDs in /jobs:', missing.length ? missing : 'NONE');

  // 2. Check the API with type=internship
  const api = await get('http://127.0.0.1:5000/api/jobs?type=internship');
  const data = JSON.parse(api.body);
  const allIntern = data.jobs.every(j => j.is_internship === true);
  console.log('API ?type=internship -> count:', data.count, '| all internships:', allIntern);

  // 3. Check default API
  const api2 = await get('http://127.0.0.1:5000/api/jobs');
  const data2 = JSON.parse(api2.body);
  console.log('API default -> count:', data2.count);
})();
