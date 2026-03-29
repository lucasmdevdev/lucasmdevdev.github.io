const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  console.log('Opening Proton Mail...');
  await page.goto('https://mail.protonmail.com/inbox', { timeout: 30000 });
  
  await page.waitForTimeout(2000);
  console.log('⚠️ Please log in manually if needed, then check for Liberapay/Ko-fi emails');
  
  // Attendre l'action manuelle
  await page.waitForTimeout(10000);
  
  // Chercher les emails de confirmation
  const emails = await page.locator('text=/Liberapay|Ko-fi/i').count();
  console.log(`Found ${emails} confirmation emails`);
  
  await browser.close();
})();
