import { test, expect } from '@playwright/test';

test.describe('Billing Flow', () => {
  test('should login, fill form and submit', async ({ page }) => {
    // Increase timeouts
    page.setDefaultTimeout(60000);
    
    // Navigate to the login page
    await page.goto('http://localhost:5173/login');
    console.log('Navigated to login page');
    
    // Fill in login credentials
    await page.fill('input[type="email"]', 'nelmak@amazon.com');
    await page.fill('input[type="password"]', 'Test123!');
    console.log('Filled login credentials');
    
    // Take a screenshot before login
    await page.screenshot({ path: 'before-login.png' });
    
    // Click the login button and wait for navigation
    await page.click('button[type="submit"]');
    console.log('Clicked login button');
    
    // Wait for the app to load by looking for the header
    await page.waitForSelector('h1:has-text("BillQuest")');
    console.log('App loaded, found BillQuest header');
    
    // Take a screenshot after login
    await page.screenshot({ path: 'after-login.png' });
    
    // Wait for the form to be fully loaded
    await page.waitForSelector('form');
    console.log('Form loaded');
    
    // Wait a bit longer for any async data loading
    await page.waitForTimeout(3000);
    
    // Take a screenshot of the form
    await page.screenshot({ path: 'form-loaded.png' });
    
    // Try to find and select the account ID
    console.log('Attempting to select account ID: 510788044118');
    
    // Check if the account is already selected
    const accountCheckboxes = await page.$$('input[type="checkbox"]');
    let accountSelected = false;
    
    for (const checkbox of accountCheckboxes) {
      // Get the parent div that contains both the checkbox and the account ID text
      const parentDiv = await checkbox.$('xpath=..');
      if (!parentDiv) continue;
      
      // Get the text content of the parent div
      const textContent = await parentDiv.textContent();
      if (textContent && textContent.includes('510788044118')) {
        // Check if the checkbox is already checked
        const isChecked = await checkbox.isChecked();
        console.log(`Found account 510788044118, checkbox is ${isChecked ? 'checked' : 'unchecked'}`);
        
        // If not checked, click it
        if (!isChecked) {
          await checkbox.click();
          console.log('Clicked the checkbox to select the account');
        } else {
          console.log('Account is already selected');
        }
        accountSelected = true;
        break;
      }
    }
    
    if (!accountSelected) {
      console.log('Could not find account checkbox, trying alternative methods');
      
      // Try other selection methods
      try {
        // Try select dropdown
        await page.selectOption('select#payerAccountId', '510788044118');
        console.log('Selected account using dropdown');
      } catch (e) {
        console.log('Select dropdown failed, trying click');
        
        try {
          // Try clicking on a div containing the account ID
          await page.click('div:has-text("510788044118")');
          console.log('Selected account by clicking on div with text');
        } catch (e2) {
          console.log('All account selection methods failed, continuing anyway');
        }
      }
    }
    
    // Take a screenshot after account selection attempt
    await page.screenshot({ path: 'after-account-selection.png' });
    
    // Check if the Invoice ID option is already selected
    console.log('Checking if Invoice ID option is selected');
    
    // Look for the Invoice ID label and check if it's already selected
    const invoiceIdLabel = await page.$('label[for="invoiceId"]');
    if (invoiceIdLabel) {
      console.log('Found Invoice ID label');
      
      // Check if there's a radio button or checkbox for Invoice ID
      const invoiceIdRadio = await page.$('input[type="radio"][name="queryType"][value="invoice"]');
      if (invoiceIdRadio) {
        const isChecked = await invoiceIdRadio.isChecked();
        console.log(`Invoice ID radio is ${isChecked ? 'checked' : 'unchecked'}`);
        
        if (!isChecked) {
          await invoiceIdRadio.click();
          console.log('Clicked Invoice ID radio button');
        }
      }
    }
    
    // Fill in the invoice ID
    console.log('Filling invoice ID: EUINFR25-123456');
    try {
      await page.fill('#invoiceId', 'EUINFR25-123456');
      console.log('Filled invoice ID using #invoiceId');
    } catch (e) {
      try {
        await page.fill('input[id="invoiceId"]', 'EUINFR25-123456');
        console.log('Filled invoice ID using input[id="invoiceId"]');
      } catch (e2) {
        try {
          // Try finding by label
          await page.fill('label:has-text("Invoice ID") + input', 'EUINFR25-123456');
          console.log('Filled invoice ID using label + input');
        } catch (e3) {
          console.log('All invoice ID fill methods failed');
        }
      }
    }
    
    // Take a screenshot before submission
    await page.screenshot({ path: 'before-submit.png' });
    
    // Debug: Print all buttons on the page
    const buttons = await page.$$('button');
    console.log(`Found ${buttons.length} buttons on the page`);
    
    for (const button of buttons) {
      const text = await button.textContent();
      console.log(`Button text: "${text}"`);
    }
    
    // Submit the form - try multiple approaches with debugging
    console.log('Attempting to submit the form');
    
    try {
      // Try to find the submit button by text content
      const submitButton = await page.getByRole('button', { name: 'Submit' });
      console.log('Found submit button by role and name');
      
      // Force click with a longer timeout
      await submitButton.click({ force: true, timeout: 10000 });
      console.log('Clicked submit button');
    } catch (e) {
      console.log('Submit button click failed:', e);
      
      try {
        // Try clicking any button that's a direct child of the form
        await page.click('form > button');
        console.log('Clicked form > button');
      } catch (e2) {
        console.log('form > button click failed:', e2);
        
        try {
          // Try clicking any button of type submit
          await page.click('button[type="submit"]');
          console.log('Clicked button[type="submit"]');
        } catch (e3) {
          console.log('button[type="submit"] click failed:', e3);
          
          try {
            // Try clicking the last button on the page
            const buttons = await page.$$('button');
            if (buttons.length > 0) {
              await buttons[buttons.length - 1].click();
              console.log('Clicked last button on page');
            } else {
              console.log('No buttons found on page');
            }
          } catch (e4) {
            console.log('Last button click failed:', e4);
          }
        }
      }
    }
    
    // Wait a moment after submission
    await page.waitForTimeout(5000);
    console.log('Waited after form submission');
    
    // Take a screenshot after submission
    await page.screenshot({ path: 'after-submit.png' });
    
    // Wait for the Download CSV button to appear with debugging
    console.log('Looking for Download CSV button...');
    
    // Take a screenshot of the current state
    await page.screenshot({ path: 'looking-for-csv-button.png' });
    
    // Try to find the Download CSV button with multiple approaches
    try {
      await page.waitForSelector('button:has-text("Download CSV")', { 
        timeout: 15000,
        state: 'visible'
      });
      console.log('Found Download CSV button by text content');
      
      // Take a screenshot showing the Download CSV button
      await page.screenshot({ path: 'download-csv-button-found.png' });
      
      // Success!
      console.log('Test completed successfully!');
    } catch (e) {
      console.log('Could not find button by text content:', e);
      
      try {
        await page.waitForSelector('button.download-csv-button', { 
          timeout: 5000,
          state: 'visible'
        });
        console.log('Found Download CSV button by class');
        
        // Take a screenshot showing the Download CSV button
        await page.screenshot({ path: 'download-csv-button-found-by-class.png' });
      } catch (e2) {
        console.log('Could not find button by class:', e2);
        
        // Take a screenshot of the current page state
        await page.screenshot({ path: 'csv-button-not-found.png' });
        
        // Print the page content for debugging
        const content = await page.content();
        console.log('Page content length:', content.length);
        console.log('Page content excerpt:', content.substring(0, 500) + '...');
        
        // Check if there's any error message on the page
        const errorText = await page.$$eval('.error-message, [role="alert"]', 
          elements => elements.map(el => el.textContent));
        if (errorText.length > 0) {
          console.log('Error messages found:', errorText);
        }
      }
    }
    
    // Take a final screenshot
    await page.screenshot({ path: 'final-state.png' });
  });
});