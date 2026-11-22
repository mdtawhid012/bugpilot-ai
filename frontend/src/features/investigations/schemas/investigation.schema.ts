import { z } from "zod";

export function utf8Bytes(value: string): number {
  return new TextEncoder().encode(value).length;
}

export const investigationSchema = z.object({
  fixtureId: z.string().min(1, "Select a fixture."),
  report: z.string().superRefine((value, context) => {
    if (utf8Bytes(value) > 16 * 1024) {
      context.addIssue({ code: "custom", message: "Report exceeds the 16 KiB UTF-8 limit." });
    }
  }),
});
