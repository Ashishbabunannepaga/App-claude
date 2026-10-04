const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2];
const ids = Object.fromEntries(fs.readFileSync(process.argv[3], 'utf8').trim().split('\n')
  .map(l => l.split(' ')).filter(p => p.length === 2 && /^(health|motor|life|parents)$/.test(p[0])));
const BASE = 'http://localhost:8080/';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, locale: 'en-IN' });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('PAGEERROR', e.message));
  const semantics = async () => {
    await page.evaluate(() => document.querySelector('flt-semantics-placeholder')?.click());
    await sleep(600);
  };
  const shot = async (name) => { await page.mouse.move(389, 2); await sleep(1200); await page.screenshot({ path: `${OUT}/${name}.png` }); console.log('shot', name); };
  const go = async (path, wait = 9000) => { await page.goto(BASE + '#' + path); await sleep(wait); await semantics(); };
  const tap = async (name, opts = {}) => { await page.getByRole(opts.role || 'button', { name, exact: !!opts.exact }).first().click(); await sleep(opts.wait || 1500); };
  const wheel = async (dy) => { await page.mouse.move(195, 500); await page.mouse.wheel(0, dy); await sleep(1200); };

  await go('/', 12000);
  await shot('01-welcome');
  await tap('Skip');
  await semantics();
  await page.getByRole('textbox').first().click(); await sleep(400);
  await page.keyboard.type('9876543210'); await sleep(400);
  await page.mouse.click(44, 414); await sleep(800);
  await shot('02-login');
  await tap('Get OTP', { wait: 2500 });
  await semantics();
  await shot('03-otp');
  await page.getByRole('textbox').first().click(); await sleep(300);
  await page.keyboard.type('246810');
  await sleep(5000); await semantics();
  await shot('04-home');
  await wheel(1400);
  await shot('05-home-scrolled');

  await go('/portfolio'); await shot('06-portfolio');
  await go(`/policy/${ids.health}`); await shot('07-policy-detail');
  await wheel(1300); await shot('08-policy-summary');
  await wheel(1500); await shot('09-policy-details');
  await go(`/policy/${ids.health}/health`); await shot('10-policy-health');
  await wheel(2000); await shot('11-policy-health-more');
  await go(`/policy/${ids.health}/ask`); await shot('12-ask-ai');
  await go(`/policy/${ids.motor}`); await shot('14-motor-detail');
  await tap('Renewal', { wait: 2000 }); await shot('15-renewal');
  await page.keyboard.press('Escape'); await sleep(1000);
  await go(`/policy/${ids.health}`); await tap('Claim help', { wait: 2500 }); await shot('16-claim-help');
  await go(`/policy/${ids.motor}/health`); await shot('17-motor-health');
  await go('/add'); await shot('18-add-policy');
  await go(`/policy/${ids.parents}/verify`); await shot('19-verify-extracted');
  await wheel(1500); await shot('20-verify-extracted-more');
  await go('/notifications'); await shot('21-notifications');
  await go('/family'); await shot('22-family');
  await go('/explore'); await shot('23-explore');
  await go('/profile'); await shot('24-profile');
  await go('/support'); await shot('25-support');
  await go('/privacy'); await shot('26-privacy');
  await go('/settings/notifications'); await shot('27-notification-settings');
  await go(`/policy/${ids.life}`); await shot('28-life-detail');

  const admin = await browser.newPage({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2 });
  await admin.goto('http://localhost:8000/admin');
  await admin.fill('#token', 'demo-admin-token-0123456789abcdef0123');
  await admin.click('text=Open'); await sleep(2000);
  await admin.screenshot({ path: `${OUT}/29-admin.png`, fullPage: true }); console.log('shot admin');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
