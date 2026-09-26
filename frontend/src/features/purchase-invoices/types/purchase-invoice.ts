import type { PurchaseInvoiceItem } from "./purchase-invoice-item";

export type PurchaseInvoice = {
  id: string;
  company: string;
  invoice_number: string;
  branch: string;
  supplier: string;
  warehouse: string;
  status: string;
  invoice_date: string;
  vendor_bill_number: string | null;
  total_amount: string;
  journal_entry?: string | null;
  shipping_cost: string;
  clearance_cost: string;
  commission_percentage: string;
  notes: string | null;
  items: PurchaseInvoiceItem[];
  created_at: string;
  updated_at: string;
};
