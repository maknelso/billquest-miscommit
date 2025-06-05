// API Request Types

export interface QueryParams {
  queryType: 'account' | 'date' | 'invoice';
  accountId?: string;
  billPeriodStartDate?: string;
  invoiceId?: string;
  date?: string;
  product?: string;
  format?: 'json' | 'csv';
}

export interface UserAccountsParams {
  email: string;
}

// API Response Types

export interface ApiErrorResponse {
  error: string;
  message: string;
  requestId: string;
}

export interface BillingDataItem {
  payer_account_id: string;
  invoice_id: string;
  product_code: string;
  bill_period_start_date: string;
  cost_before_tax: number;
  credits_before_discount?: number;
  credits_after_discount?: number;
  sp_discount?: number;
  ubd_discount?: number;
  prc_discount?: number;
  rvd_discount?: number;
  edp_discount?: number;
  edp_discount_percent?: number;
  [key: string]: any; // For any additional fields
}

export interface DataSummary {
  unique_accounts: number;
  unique_invoices: number;
  unique_dates: number;
  unique_products: number;
  total_cost: number;
}

export interface QueryDataResponse {
  data: {
    items: BillingDataItem[];
    count: number;
    summary: DataSummary;
  };
}

export interface UserAccountsResponse {
  data: {
    email: string;
    payer_account_ids: string[];
  };
}