const { chromium } = require('playwright');

async function maybeClick(page, selectors) {
  for (const s of selectors) {
    try {
      const el = page.locator(s).first();
      if (await el.isVisible({ timeout: 1500 })) {
        await el.click({ timeout: 2000 });
        await page.waitForTimeout(1000);
        return true;
      }
    } catch {}
  }
  return false;
}

(async () => {
  const [url, outPath, mode = 'header'] = process.argv.slice(2);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1800 } });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await page.waitForTimeout(5000);

  await maybeClick(page, [
    'button:has-text("Continue")',
    'button:has-text("Accept")',
    'button:has-text("Accept All")',
    'button:has-text("I Accept")',
    '[aria-label="Accept"]',
  ]);

  if (url.includes('cnbc.com')) {
    await maybeClick(page, [
      'button:has-text("Continue")',
      'button:has-text("Close")',
      '[data-testid="privacy-banner-accept"]',
    ]);
  }

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(1000);

  let clip = null;
  if (mode === 'header') {
    clip = { x: 0, y: 0, width: 1440, height: 1500 };
  } else if (mode === 'hero') {
    clip = { x: 0, y: 0, width: 1440, height: 1900 };
  }

  await page.screenshot({ path: outPath, ...(clip ? { clip } : {}) });
  await browser.close();
})();
