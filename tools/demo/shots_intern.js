// Setup-guide screenshots (docs/screenshots/v3): English (light), Hindi, dark. Usage: node shots_intern.js <outdir> <ids.txt>
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2];
const ids = Object.fromEntries(fs.readFileSync(process.argv[3], 'utf8').trim().split('\n').map(l => l.split(' ')).filter(p => p.length === 2));
const BASE = 'http://localhost:8080/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, locale: 'en-IN' });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('PAGEERROR', e.message));
  const semantics = async () => { await page.evaluate(() => document.querySelector('flt-semantics-placeholder')?.click()); await sleep(600); };
  const shot = async (name) => { await page.mouse.move(389, 2); await sleep(1400); await page.screenshot({ path: `${OUT}/${name}.png` }); console.log('shot', name); };
  const go = async (path, wait = 9000) => { await page.goto(BASE + '#' + path); await sleep(wait); await semantics(); };
  const tap = async (name, opts = {}) => { await page.getByRole(opts.role || 'button', { name, exact: !!opts.exact }).first().click(); await sleep(opts.wait || 1500); };
  const wheel = async (dy) => { await page.mouse.move(195, 600); await page.mouse.wheel(0, dy); await sleep(1200); };
  const prefs = async (locale, theme) => { await page.evaluate(([l, t]) => { localStorage.setItem('flutter.app_locale', JSON.stringify(l)); localStorage.setItem('flutter.theme_mode', JSON.stringify(t)); }, [locale, theme]); await page.reload(); await sleep(12000); await semantics(); };

  // English, light
  await go('/', 12000);
  await shot('01-welcome');
  await tap('Skip', { wait: 2500 }); await semantics();
  await shot('02-login');
  await page.getByRole('textbox').first().click(); await sleep(300);
  await page.keyboard.type('9876543210'); await sleep(300);
  const box = await page.getByRole('checkbox').first().boundingBox();
  await page.mouse.click(box.x + 22, box.y + box.height / 2); await sleep(600);
  await tap('Get OTP', { wait: 2500 }); await semantics();
  await shot('03-otp');
  await page.getByRole('textbox').first().click(); await sleep(300);
  await page.keyboard.type('246810'); await sleep(6000); await semantics();
  await shot('04-home');
  await wheel(650); await shot('05-home-more');
  await go('/portfolio'); await shot('06-portfolio');
  await go(`/policy/${ids.health}`); await shot('07-policy-detail');
  await go(`/policy/${ids.health}/report`); await shot('08-coverage-report');
  await go(`/policy/${ids.health}/ask`); await shot('09-ask-ai');
  await go(`/policy/${ids.health}/verify`); await shot('10-check-details');
  await go(`/policy/${ids.life}/nominees`); await shot('11-nominees');
  await go('/add'); await shot('12-add-policy');
  await go('/emergency'); await shot('13-emergency');
  await go('/explore'); await shot('14-explore');
  await go('/profile'); await shot('15-profile');
  // Hindi
  await prefs('hi', 'light');
  await go('/', 12000); await shot('20-hi-home');
  await go(`/policy/${ids.health}`); await shot('21-hi-policy-detail');
  await go('/profile'); await shot('22-hi-profile');
  // Dark
  await prefs('en', 'dark');
  await go('/', 12000); await shot('30-dark-home');
  await go(`/policy/${ids.health}`); await shot('31-dark-policy-detail');
  await go(`/policy/${ids.health}/report`); await shot('32-dark-coverage-report');
  await go('/profile'); await shot('33-dark-profile');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
