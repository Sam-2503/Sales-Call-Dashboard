import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { copy } from "@/copy";
import { AppBanners } from "@/shell/AppBanners";

afterEach(() => {
  Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
  vi.restoreAllMocks();
});

describe("shell banners", () => {
  it("shows the offline banner after the browser goes offline", () => {
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    render(<AppBanners />);
    expect(screen.getByText(copy.shell.offlineTitle)).toBeInTheDocument();
    expect(screen.getByText(copy.shell.offlineBody)).toBeInTheDocument();
  });

  it("offers a new tab when the app is embedded", () => {
    vi.spyOn(window, "top", "get").mockReturnValue({} as Window);
    render(<AppBanners />);
    expect(screen.getByText(copy.shell.embeddedTitle)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: copy.shell.openNewTab })).toHaveAttribute(
      "target",
      "_blank",
    );
  });
});
