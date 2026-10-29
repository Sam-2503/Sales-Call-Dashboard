import { expect } from "vitest";
import { axe } from "vitest-axe";

export async function expectNoAxeViolations(container: Element): Promise<void> {
  const results = await axe(container, {
    rules: {
      region: { enabled: false },
      "color-contrast": { enabled: false },
    },
  });
  expect(results.violations).toEqual([]);
}
