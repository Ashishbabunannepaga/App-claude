// Renders out/print/*.svg and out/proof/*.svg to PDFs at their exact physical size (fonts embedded, vectors kept),
// plus a PNG preview of each proof. Run after build.py:  node render_pdf.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, 'out');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const dir of ['print', 'proof']) {
    for (const f of fs.readdirSync(path.join(OUT, dir)).filter((f) => f.endsWith('.svg'))) {
      const svg = fs.readFileSync(path.join(OUT, dir, f), 'utf8');
      const [, w, h] = svg.match(/width="([\d.]+)mm" height="([\d.]+)mm"/);
      await page.setContent(
        `<style>@page{size:${w}mm ${h}mm;margin:0}html,body{margin:0}svg{display:block}</style>${svg}`,
      );
      await page.evaluate(() => document.fonts.ready);
      await page.pdf({ path: path.join(OUT, dir, f.replace('.svg', '.pdf')), width: `${w}mm`, height: `${h}mm`, printBackground: true });
      if (dir === 'proof') {
        const scale = 1200 / (parseFloat(w) * 3.7795);
        await page.setViewportSize({ width: 1200, height: Math.ceil(parseFloat(h) * 3.7795 * scale) });
        await page.setContent(`<style>html,body{margin:0}svg{display:block;width:1200px;height:auto}</style>${svg}`);
        await page.evaluate(() => document.fonts.ready);
        await page.screenshot({ path: path.join(OUT, dir, f.replace('.svg', '.png')), fullPage: true });
      }
      console.log(`${dir}/${f} -> ${w} x ${h} mm`);
    }
  }
  await browser.close();
})();
