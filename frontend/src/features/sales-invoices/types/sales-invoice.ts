import type { SalesInvoiceItem } from "./sales-invoice-item";

export type SalesInvoice = {
  id: string;
  company: string;
  branch: string;
  invoice_number: string;
  customer: string;
  warehouse: string;
  date: string;
  status: string;
  total_amount: string;
  journal_entry?: string | null;
  notes: string | null;
  items: SalesInvoiceItem[];
  created_at: string;
  updated_at: string;
};
