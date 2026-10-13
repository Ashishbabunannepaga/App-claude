// Renders the icon SVGs to PNG with the preinstalled Chromium: node render.js
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1024, height: 1024 } });
  for (const name of ['icon', 'icon-foreground']) {
    const svg = fs.readFileSync(`${__dirname}/${name}.svg`, 'utf8');
    await page.setContent(`<html><body style="margin:0;background:transparent">${svg}</body></html>`);
    await page.locator('svg').screenshot({ path: `${__dirname}/${name}-1024.png`, omitBackground: true });
  }
  await browser.close();
})();
