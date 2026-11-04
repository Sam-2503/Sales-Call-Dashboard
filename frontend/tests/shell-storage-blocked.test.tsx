import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { copy } from "@/copy";

vi.mock("@/api/storage", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/api/storage")>();
  return { ...actual, storageAvailable: false };
});

import { setAccessKey } from "@/api/storage";
import { renderRoute } from "./helpers/renderRoute";

describe("blocked browser storage", () => {
  it("keeps the app usable and warns that the key will not be remembered", async () => {
    renderRoute("/");
    expect(
      await screen.findByRole("heading", { level: 1, name: copy.welcome.headline }),
    ).toBeInTheDocument();
    expect(screen.getByText(copy.shell.storageTitle)).toBeInTheDocument();
  });

  it("offers a copy control when a key is present", async () => {
    setAccessKey("mock-access-key");
    renderRoute("/calls");
    expect(await screen.findByRole("heading", { name: copy.calls.title })).toBeInTheDocument();
    expect(screen.getByText(copy.shell.storageTitle)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: copy.shell.copyKey })).toBeInTheDocument();
  });
});
