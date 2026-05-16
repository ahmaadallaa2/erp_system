import { useEffect, useState } from "react";
import { useParams } from "react-router";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  SectionCard,
  StatusBadge,
} from "../../../components/ui/mvp";
import { theme } from "../../../styles/theme";
import { getJournalEntry } from "../api/get-journal-entry";
import type { JournalEntryDetail } from "../types";

function JournalEntryDetailPage() {
  const { id } = useParams();
  const [entry, setEntry] = useState<JournalEntryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadJournalEntry() {
      if (!id) {
        setError("Journal entry ID is missing.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");
        const data = await getJournalEntry(id);
        setEntry(data);
      } catch (err) {
        console.error("Journal entry load error:", err);
        setError("Failed to load journal entry.");
      } finally {
        setLoading(false);
      }
    }

    loadJournalEntry();
  }, [id]);

  if (loading) {
    return <LoadingState label="Loading journal entry..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (!entry) {
    return <EmptyState title="Journal entry not found" />;
  }

  return (
    <main>
      <PageHeader
        title={entry.entry_number}
        subtitle={`${entry.journal.code} - ${entry.journal.name}`}
        actions={<StatusBadge status={entry.status} />}
      />

      <SectionCard title="Journal Summary">
        <div style={summaryGridStyle}>
          <InfoRow label="Journal" value={`${entry.journal.code} - ${entry.journal.name}`} />
          <InfoRow label="Journal Type" value={entry.journal.type} />
          <InfoRow label="Date" value={entry.date} />
          <InfoRow label="Reference" value={entry.reference || "-"} />
          <InfoRow label="Description" value={entry.description || "-"} />
          <InfoRow label="Total Debit" value={entry.total_debit} />
          <InfoRow label="Total Credit" value={entry.total_credit} />
        </div>
      </SectionCard>

      <SectionCard title="Journal Lines">
        {entry.items.length === 0 ? (
          <EmptyState title="No journal lines found" />
        ) : (
          <div style={tableCardStyle}>
            <table style={tableStyle}>
              <thead style={tableHeadStyle}>
                <tr>
                  <th style={thStyle}>Account Code</th>
                  <th style={thStyle}>Account Name</th>
                  <th style={thStyle}>Partner Name</th>
                  <th style={thStyle}>Description</th>
                  <th style={rightThStyle}>Debit</th>
                  <th style={rightThStyle}>Credit</th>
                </tr>
              </thead>
              <tbody>
                {entry.items.map((line) => (
                  <tr key={line.id}>
                    <td style={tdStyle}>{line.account_code}</td>
                    <td style={tdStyle}>{line.account_name}</td>
                    <td style={tdStyle}>{line.partner_name || "-"}</td>
                    <td style={tdStyle}>{line.description || "-"}</td>
                    <td style={rightTdStyle}>{line.debit}</td>
                    <td style={rightTdStyle}>{line.credit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </main>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div style={infoLabelStyle}>{label}</div>
      <div style={infoValueStyle}>{value}</div>
    </div>
  );
}

const summaryGridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: "16px",
};

const infoLabelStyle: React.CSSProperties = {
  marginBottom: "6px",
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const infoValueStyle: React.CSSProperties = {
  color: theme.colors.textPrimary,
  fontWeight: 600,
};

const tableCardStyle: React.CSSProperties = {
  overflowX: "auto",
  border: `1px solid ${theme.colors.border}`,
  borderRadius: "8px",
};

const tableStyle: React.CSSProperties = {
  width: "100%",
  borderCollapse: "collapse",
};

const tableHeadStyle: React.CSSProperties = {
  background: "#f8fafc",
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "12px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  color: theme.colors.textSecondary,
  fontSize: "13px",
};

const rightThStyle: React.CSSProperties = {
  ...thStyle,
  textAlign: "right",
};

const tdStyle: React.CSSProperties = {
  padding: "13px 14px",
  borderBottom: `1px solid ${theme.colors.border}`,
  color: theme.colors.textPrimary,
  fontSize: "14px",
};

const rightTdStyle: React.CSSProperties = {
  ...tdStyle,
  textAlign: "right",
  fontVariantNumeric: "tabular-nums",
};

export default JournalEntryDetailPage;
