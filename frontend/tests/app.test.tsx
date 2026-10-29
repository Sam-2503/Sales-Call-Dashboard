import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "@/App";
import { ToastProvider } from "@/components";
import { copy, technicalCopy } from "@/copy";

import { expectNoAxeViolations } from "./axe";

function renderApp() {
  return render(
    <ToastProvider>
      <App />
    </ToastProvider>,
  );
}

describe("application shell", () => {
  it("renders the preview in light and dark themes without axe violations", async () => {
    const user = userEvent.setup();
    renderApp();

    expect(screen.getByRole("heading", { level: 1, name: copy.preview.title })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: copy.common.skipToContent })).toBeInTheDocument();
    await expectNoAxeViolations(document.body);

    await user.click(screen.getByRole("button", { name: copy.preview.themeDark }));
    await waitFor(() => expect(document.documentElement).toHaveAttribute("data-theme", "dark"));
    expect(screen.getByRole("button", { name: copy.preview.themeDark })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expectNoAxeViolations(document.body);

    await user.click(screen.getByRole("button", { name: copy.preview.themeLight }));
    await waitFor(() => expect(document.documentElement).toHaveAttribute("data-theme", "light"));
    await expectNoAxeViolations(document.body);

    await user.click(screen.getByRole("button", { name: copy.preview.themeSystem }));
    await waitFor(() => expect(document.documentElement).not.toHaveAttribute("data-theme"));
  });

  it("shows the AI honesty note once and keeps technical terms collapsed", () => {
    renderApp();
    expect(screen.getAllByText(copy.feedback.honesty)).toHaveLength(1);
    expect(screen.queryByText(technicalCopy.pipelineVersion)).not.toBeInTheDocument();
  });
});
