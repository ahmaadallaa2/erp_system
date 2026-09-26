import axios from "axios";

const FALLBACK_MESSAGE = "Something went wrong. Please try again.";

export function getApiErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return FALLBACK_MESSAGE;
  }

  const data = error.response?.data;
  const message = formatDrfError(data);

  return message || error.message || FALLBACK_MESSAGE;
}

function formatDrfError(data: unknown): string {
  if (!data) return "";

  if (typeof data === "string") {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map(formatDrfError).filter(Boolean).join(" ");
  }

  if (typeof data !== "object") {
    return String(data);
  }

  const record = data as Record<string, unknown>;
  const detail = formatDrfError(record.detail);
  if (detail) return detail;

  const nonFieldErrors = formatDrfError(record.non_field_errors);
  if (nonFieldErrors) return nonFieldErrors;

  return Object.entries(record)
    .filter(([key]) => key !== "detail" && key !== "non_field_errors")
    .map(([key, value]) => {
      const fieldMessage = formatDrfError(value);
      return fieldMessage ? `${formatFieldName(key)}: ${fieldMessage}` : "";
    })
    .filter(Boolean)
    .join(" ");
}

function formatFieldName(fieldName: string) {
  return fieldName.replace(/_/g, " ");
}
