// CapitUp v2 screenshots. Usage:
//   node shots_v2.js <outdir> new               (empty demo account: welcome, login, new-user home, sample report, rewards)
//   node shots_v2.js <outdir> seeded <ids.txt>  (after seed.py: home, portfolio, detail, report, emergency)
const { chromium } = require('playwright');
const fs = require('fs');
const OUT = process.argv[2];
const MODE = process.argv[3];
const ids = MODE === 'seeded'
  ? Object.fromEntries(fs.readFileSync(process.argv[4], 'utf8').trim().split('\n').map(l => l.split(' ')).filter(p => p.length === 2))
  : {};
const BASE = 'http://localhost:8080/';
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, locale: 'en-IN' });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('PAGEERROR', e.message));
  const semantics = async () => { await page.evaluate(() => document.querySelector('flt-semantics-placeholder')?.click()); await sleep(600); };
  const shot = async (name) => { await page.mouse.move(389, 2); await sleep(1400); await page.screenshot({ path: `${OUT}/${name}.png` }); console.log('shot', name); };
  const go = async (path, wait = 9000) => { await page.goto(BASE + '#' + path); await sleep(wait); await semantics(); };
  const tap = async (name, opts = {}) => { await page.getByRole(opts.role || 'button', { name, exact: !!opts.exact }).first().click(); await sleep(opts.wait || 1500); };
  const wheel = async (dy) => { await page.mouse.move(195, 700); await page.mouse.wheel(0, dy); await sleep(1200); };

  const login = async () => {
    await page.getByRole('textbox').first().click(); await sleep(300);
    await page.keyboard.type('9876543210'); await sleep(300);
    const box = await page.getByRole('checkbox').first().boundingBox();
    await page.mouse.click(box.x + 22, box.y + box.height / 2); await sleep(600);
    await tap('Get OTP', { wait: 2500 }); await semantics();
    await page.getByRole('textbox').first().click(); await sleep(300);
    await page.keyboard.type('246810'); await sleep(5000); await semantics();
  };

  if (MODE === 'new') {
    await go('/', 12000);
    await shot('v2-01-welcome-1');
    await tap('Next', { wait: 1200 }); await shot('v2-02-welcome-2');
    await tap('Next', { wait: 1200 }); await shot('v2-03-welcome-3');
    await tap('Next', { wait: 1200 }); await shot('v2-04-welcome-4');
    await tap('Get started', { wait: 2500 }); await semantics();
    await shot('v2-05-login');
    await login();
    const name = page.getByRole('textbox').first();
    if (await name.count()) {
      await name.click(); await sleep(300); await page.keyboard.type('Asha Rao'); await sleep(300);
      await tap('Continue', { wait: 5000 }); await semantics();
    }
    await sleep(2500);
    await shot('v2-06-home-new');
    await wheel(700); await shot('v2-07-home-new-more');
    await go('/report/sample'); await shot('v2-08-sample-report');
    await wheel(800); await shot('v2-09-sample-report-rows');
    await go('/rewards'); await shot('v2-10-rewards');
    await go('/emergency'); await shot('v2-11-emergency-empty');
    await go('/portfolio'); await shot('v2-12-portfolio-empty');
  } else {
    await go('/', 12000);
    await tap('Skip', { wait: 2000 }); await semantics();
    await login();
    await sleep(2500);
    await shot('v2-20-home');
    await wheel(650); await shot('v2-21-home-2');
    await wheel(700); await shot('v2-22-home-3');
    await go('/portfolio'); await shot('v2-23-portfolio');
    await go(`/policy/${ids.health}/report`); await shot('v2-24-report-own');
    await go('/emergency'); await shot('v2-25-emergency');
    await go(`/policy/${ids.motor}/report`); await wheel(1500); await shot('v2-26-report-motor-addons');
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
