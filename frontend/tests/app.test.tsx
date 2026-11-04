import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { setAccessKey } from "@/api/storage";
import { copy, technicalCopy } from "@/copy";

import { expectNoAxeViolations } from "./axe";
import { renderRoute } from "./helpers/renderRoute";

describe("welcome and access", () => {
  it("creates the workspace on the first click, not on page load", async () => {
    const user = userEvent.setup();
    renderRoute("/");

    expect(
      screen.getByRole("heading", { level: 1, name: copy.welcome.headline }),
    ).toBeInTheDocument();
    expect(localStorage.getItem("call-review.access-key")).toBeNull();
    await screen.findByText(copy.welcome.privacyRetention(30));

    await user.click(screen.getByRole("button", { name: copy.welcome.upload }));

    await screen.findByRole("heading", { name: copy.calls.title });
    expect(await screen.findByText(copy.calls.emptyTitle)).toBeInTheDocument();
    expect(localStorage.getItem("call-review.access-key")).toBe("mock-access-key");
  });

  it("starts a sample and opens its first call", async () => {
    const user = userEvent.setup();
    const { router } = renderRoute("/");

    await user.click(await screen.findByRole("button", { name: copy.welcome.trySample }));

    await screen.findByRole("heading", { level: 1, name: "Sample: Acme discovery" });
    expect(router.state.location.pathname).toBe(`/calls/c6666666-6666-4666-8666-666666666666`);
  });

  it("rejects a bad access key and accepts a good one", async () => {
    const user = userEvent.setup();
    renderRoute("/");

    await user.click(screen.getByRole("button", { name: copy.welcome.haveKey }));
    const input = await screen.findByLabelText(copy.welcome.keyLabel);
    await user.type(input, "short");
    await user.click(screen.getByRole("button", { name: copy.welcome.keySubmit }));
    expect(await screen.findByRole("alert")).toHaveTextContent(copy.welcome.keyInvalid);

    await user.clear(input);
    await user.type(input, "mock-access-key");
    await user.click(screen.getByRole("button", { name: copy.welcome.keySubmit }));

    await screen.findByRole("heading", { name: copy.calls.title });
    expect(localStorage.getItem("call-review.access-key")).toBe("mock-access-key");
  });

  it("opens the restore dialog from the restore route", async () => {
    renderRoute("/?restore=1");
    expect(await screen.findByRole("dialog", { name: copy.welcome.keyTitle })).toBeInTheDocument();
  });

  it("opens and closes the access-key dialog from the keyboard", async () => {
    const user = userEvent.setup();
    renderRoute("/");

    const trigger = screen.getByRole("button", { name: copy.welcome.haveKey });
    trigger.focus();
    await user.keyboard("{Enter}");
    const dialog = await screen.findByRole("dialog", { name: copy.welcome.keyTitle });
    expect(dialog.contains(document.activeElement)).toBe(true);
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  });
});

describe("settings", () => {
  it("adds and renames a rep, changes the theme, and deletes everything", async () => {
    setAccessKey("mock-access-key");
    const user = userEvent.setup();
    renderRoute("/settings");

    expect(await screen.findByRole("heading", { name: copy.settings.title })).toBeInTheDocument();
    await screen.findByText("Me");

    await user.type(screen.getByLabelText(copy.settings.repName), "Riley");
    await user.click(screen.getByRole("button", { name: copy.settings.addSubmit }));
    expect(await screen.findByText("Riley")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: `${copy.settings.renameRep}: Riley` }));
    const renameDialog = await screen.findByRole("dialog", { name: copy.settings.renameRep });
    const renameInput = within(renameDialog).getByLabelText(copy.settings.repName);
    await user.clear(renameInput);
    await user.type(renameInput, "Riley Chen");
    await user.click(within(renameDialog).getByRole("button", { name: copy.settings.saveName }));
    expect(await screen.findByText("Riley Chen")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: copy.theme.dark }));
    await waitFor(() => expect(document.documentElement).toHaveAttribute("data-theme", "dark"));

    await user.click(screen.getByRole("button", { name: copy.settings.deleteButton }));
    const deleteDialog = await screen.findByRole("dialog", { name: copy.settings.deleteTitle });
    await user.click(
      within(deleteDialog).getByRole("button", { name: copy.settings.deleteButton }),
    );

    await screen.findByRole("heading", { level: 1, name: copy.welcome.headline });
    expect(localStorage.getItem("call-review.access-key")).toBeNull();
  });
});

describe("navigation and accessibility", () => {
  it("shows how this works without technical terms outside the collapsed block", async () => {
    renderRoute("/how-it-works");
    expect(await screen.findByRole("heading", { name: copy.howItWorks.title })).toBeInTheDocument();
    expect(screen.queryByText(technicalCopy.embeddingModel)).not.toBeInTheDocument();
    expect(await screen.findByText(copy.feedback.honesty)).toBeInTheDocument();
  });

  it("redirects the start page to calls when a key is present", async () => {
    setAccessKey("mock-access-key");
    const { router } = renderRoute("/");
    await screen.findByRole("heading", { name: copy.calls.title });
    expect(router.state.location.pathname).toBe("/calls");
  });

  it("shows a 404 with a way back", async () => {
    renderRoute("/not-a-page");
    expect(screen.getByRole("heading", { name: copy.notFound.title })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: copy.notFound.action })).toBeInTheDocument();
  });

  it.each([
    ["welcome", "/"],
    ["how it works", "/how-it-works"],
    ["404", "/not-a-page"],
  ])("passes axe on the %s page", async (_name, path) => {
    renderRoute(path);
    await screen.findByRole("heading", { level: 1 });
    await expectNoAxeViolations(document.body);
  });

  it("passes axe in dark mode", async () => {
    localStorage.setItem("call-review.theme", "dark");
    renderRoute("/");
    await screen.findByRole("heading", { level: 1 });
    await expectNoAxeViolations(document.body);
  });

  it("passes axe on calls and settings when signed in", async () => {
    setAccessKey("mock-access-key");
    const calls = renderRoute("/calls");
    await screen.findByRole("heading", { name: copy.calls.title });
    await expectNoAxeViolations(document.body);
    calls.unmount();

    renderRoute("/settings");
    await screen.findByRole("heading", { name: copy.settings.title });
    await expectNoAxeViolations(document.body);
  });

  it("passes axe on the remaining pages in dark mode", async () => {
    setAccessKey("mock-access-key");
    localStorage.setItem("call-review.theme", "dark");

    for (const [path, heading] of [
      ["/calls", copy.calls.title],
      ["/settings", copy.settings.title],
      ["/how-it-works", copy.howItWorks.title],
      ["/not-a-page", copy.notFound.title],
    ] as const) {
      const result = renderRoute(path);
      await screen.findByRole("heading", { name: heading });
      await expectNoAxeViolations(document.body);
      result.unmount();
    }
  });
});
