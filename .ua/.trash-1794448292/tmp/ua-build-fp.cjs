const fs = require('fs');
const { execSync } = require('child_process');

const root = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles';
const ua = root + '/.ua';
const scan = JSON.parse(fs.readFileSync(ua + '/intermediate/scan-result.json', 'utf8'));
const gitCommitHash = execSync(`git -C "${root}" rev-parse HEAD`, { encoding: 'utf8' }).trim();
const input = {
  projectRoot: root,
  filePaths: scan.files.map(f => f.path),
  gitCommitHash
};
fs.writeFileSync(ua + '/intermediate/fingerprint-input.json', JSON.stringify(input, null, 2));
console.log('Wrote fingerprint-input.json with', input.filePaths.length, 'paths, commit:', gitCommitHash);
