import { useState, FormEvent } from 'react';
import './App.css'; // Keep this import if you still have an App.css file, otherwise remove it

function App() {
  const [payerAccountId, setPayerAccountId] = useState<string>('');
  const [billPeriodStartDate, setBillPeriodStartDate] = useState<string>('');
  const [invoiceId, setInvoiceId] = useState<string>('');

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();

    // Basic validation for payerAccountId
    if (!payerAccountId.trim()) {
      alert('Payer Account ID is required!');
      return;
    }

    // Validation for at least one of the date or invoice ID
    if (!billPeriodStartDate.trim() && !invoiceId.trim()) {
        alert('Please provide either a Bill Period Start Date OR an Invoice ID.');
        return;
    }


    console.log('Form Submitted!');
    console.log('Payer Account ID:', payerAccountId);

    if (billPeriodStartDate.trim()) {
      console.log('Bill Period Start Date:', billPeriodStartDate);
    }
    if (invoiceId.trim()) { // Use if for both to allow both, or else if if strictly one or the other
      console.log('Invoice ID:', invoiceId);
    }

    // Optional: Clear the form fields after submission
    setPayerAccountId('');
    setBillPeriodStartDate('');
    setInvoiceId('');
  };

  return (
    <div className="app-container">
      <form onSubmit={handleSubmit} className="billing-form">
        <h2>Bill Information Request</h2>

        <div className="form-group">
          <label htmlFor="payerAccountId">Payer Account ID: (required)</label> {/* Added (required) */}
          <input
            type="text"
            id="payerAccountId"
            value={payerAccountId}
            onChange={(e) => setPayerAccountId(e.target.value)}
            required
          />
        </div>

        {/* Removed the <p className="or-separator">OR</p> */}

        <p className="choose-one-text">Choose at least ONE of the below:</p> {/* New instruction text */}

        <div className="form-group">
          <label htmlFor="billPeriodStartDate">Bill Period Start Date:</label> {/* Label simplified */}
          <input
            type="text"
            id="billPeriodStartDate"
            value={billPeriodStartDate}
            onChange={(e) => setBillPeriodStartDate(e.target.value)}
            placeholder="e.g. 01-25"
          />
        </div>

        <div className="form-group">
          <label htmlFor="invoiceId">Invoice ID:</label> {/* Label simplified */}
          <input
            type="text"
            id="invoiceId"
            value={invoiceId}
            onChange={(e) => setInvoiceId(e.target.value)}
            placeholder="e.g. EUINFR25-123456"
          />
        </div>

        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

export default App;