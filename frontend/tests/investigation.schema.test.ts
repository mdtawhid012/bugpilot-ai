import { describe, expect, it } from "vitest";
import { investigationSchema, utf8Bytes } from "@/features/investigations/schemas/investigation.schema";

describe("investigation form schema", () => {
  it("accepts an empty report but rejects a UTF-8 report over 16 KiB", () => {
    expect(investigationSchema.safeParse({ fixtureId: "discount-calculator", report: "" }).success).toBe(true);
    expect(investigationSchema.safeParse({ fixtureId: "discount-calculator", report: "😀".repeat(4097) }).success).toBe(false);
  });

  it("counts UTF-8 bytes rather than JavaScript characters", () => {
    expect(utf8Bytes("😀")).toBe(4);
  });
});
