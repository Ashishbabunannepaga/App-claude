// New-user screens (run BEFORE seed.py, while the demo account has no policies):
// home hero, sample coverage reports and the rewards wallet.
const { chromium } = require('playwright');
const OUT = process.argv[2];
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
  const wheel = async (dy) => { await page.mouse.move(195, 760); await page.mouse.wheel(0, dy); await sleep(1200); };

  await go('/', 12000);
  await shot('38-welcome-brand');
  await tap('Skip');
  await semantics();
  await page.getByRole('textbox').first().click(); await sleep(400);
  await page.keyboard.type('9876543210'); await sleep(400);
  await page.mouse.click(44, 414); await sleep(800);
  await tap('Get OTP', { wait: 2500 });
  await semantics();
  await page.getByRole('textbox').first().click(); await sleep(300);
  await page.keyboard.type('246810');
  await sleep(5000); await semantics();
  // First login asks for a name.
  const name = page.getByRole('textbox').first();
  if (await name.count()) {
    await name.click(); await sleep(300); await page.keyboard.type('Asha Rao'); await sleep(300);
    await tap('Continue', { wait: 5000 }); await semantics();
  }
  await sleep(2500);
  await shot('39-home-new-user');
  await wheel(900); await shot('40-home-new-user-more');

  await go('/report/sample'); await shot('41-sample-report-health');
  await wheel(700); await shot('42-sample-report-sections');
  await semantics();
  await page.getByRole('button', { name: /^Room rent:/ }).first().click(); await sleep(1500);
  await shot('44-sample-report-row-detail');
  await page.keyboard.press('Escape'); await sleep(800);
  await wheel(1100); await shot('43-sample-report-extras');
  await page.keyboard.press('Escape'); await sleep(800);
  await go('/report/sample?type=life'); await shot('45-sample-report-life');
  await wheel(900); await shot('46-sample-report-life-more');
  await go('/report/sample?type=motor'); await shot('47-sample-report-motor');
  await wheel(1100); await shot('48-sample-report-motor-more');
  await go('/rewards'); await shot('49-rewards-earn');
  await tap('USE COINS'); await shot('50-rewards-use');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
