const fs = require('fs');
const path = require('path');
const files = [
  'static/js/main.js',
  'static/js/jobs.js',
  'static/js/dashboard.js',
  'static/js/profile.js',
  'static/js/resume.js',
  'static/js/wage.js',
  'static/js/roadmap.js',
  'static/js/interview.js',
  'static/js/chatbot.js',
];
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  try {
    new Function(src); // parse-only check
    console.log('OK   ', f);
  } catch (e) {
    console.log('ERROR', f, '->', e.message);
  }
}
