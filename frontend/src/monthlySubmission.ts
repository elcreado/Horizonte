/** Keep the exact monthly request until the server gives a definitive response. */
export function createMonthlySubmission(makeId: () => string = () => crypto.randomUUID()) {
  let pending: Readonly<Record<string, string | null>> | null = null;
  return {
    capture(values: Record<string, string>) {
      pending ??= Object.freeze({ ...values, end_date: values.end_date || null, request_id: makeId() });
      return pending;
    },
    settle(status: number) {
      if (status >= 200 && status < 500) pending = null;
    },
    isPending() { return pending !== null; },
  };
}
