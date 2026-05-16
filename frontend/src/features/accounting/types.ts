export type JournalBasic = {
  id: string;
  code: string;
  name: string;
  type?: string;
};

export type JournalItemLine = {
  id: string;
  account_id: string;
  account_code: string;
  account_name: string;
  partner_id: string | null;
  partner_name: string | null;
  debit: string;
  credit: string;
  description: string;
};

export type JournalEntryDetail = {
  id: string;
  journal: JournalBasic;
  entry_number: string;
  date: string;
  status: string;
  reference: string;
  description: string;
  total_debit: string;
  total_credit: string;
  items: JournalItemLine[];
};
