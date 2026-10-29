import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import {
  Button,
  CopyButton,
  Dialog,
  Disclosure,
  EmptyState,
  ErrorState,
  InfoTip,
  Popover,
  PopoverContent,
  PopoverTrigger,
  ScoreRing,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  ToastProvider,
  Tooltip,
  useToast,
} from "@/components";
import { copy, technicalCopy } from "@/copy";

import { expectNoAxeViolations } from "./axe";

function renderMain(ui: ReactElement) {
  return render(<main>{ui}</main>);
}

describe("base components", () => {
  it("Button is reachable and activates from the keyboard", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    renderMain(<Button onClick={onClick}>{copy.preview.primaryAction}</Button>);

    await user.tab();
    expect(screen.getByRole("button", { name: copy.preview.primaryAction })).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onClick).toHaveBeenCalledTimes(1);
    await expectNoAxeViolations(document.body);
  });

  it("Dialog opens, traps focus, closes on Escape, and returns focus", async () => {
    const user = userEvent.setup();
    renderMain(
      <Dialog
        trigger={<Button>{copy.preview.dialogOpen}</Button>}
        title={copy.preview.dialogTitle}
        description={copy.preview.dialogBody}
        footer={<Button>{copy.preview.dialogConfirm}</Button>}
      >
        <p>{copy.preview.exampleBody}</p>
      </Dialog>,
    );

    const trigger = screen.getByRole("button", { name: copy.preview.dialogOpen });
    await user.click(trigger);
    const dialog = await screen.findByRole("dialog", { name: copy.preview.dialogTitle });
    expect(dialog).toBeInTheDocument();
    expect(dialog.contains(document.activeElement)).toBe(true);
    await expectNoAxeViolations(document.body);

    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(trigger).toHaveFocus();
  });

  it("Tabs switch with the arrow keys", async () => {
    const user = userEvent.setup();
    renderMain(
      <Tabs defaultValue="summary">
        <TabsList aria-label={copy.preview.tabsLabel}>
          <TabsTrigger value="summary">{copy.preview.tabSummary}</TabsTrigger>
          <TabsTrigger value="moments">{copy.preview.tabMoments}</TabsTrigger>
        </TabsList>
        <TabsContent value="summary">{copy.preview.exampleBody}</TabsContent>
        <TabsContent value="moments">{copy.preview.exampleMoment}</TabsContent>
      </Tabs>,
    );

    const summary = screen.getByRole("tab", { name: copy.preview.tabSummary });
    summary.focus();
    await user.keyboard("{ArrowRight}");
    const moments = screen.getByRole("tab", { name: copy.preview.tabMoments });
    expect(moments).toHaveFocus();
    expect(moments).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(copy.preview.exampleMoment)).toBeVisible();
    await expectNoAxeViolations(document.body);
  });

  it("Popover opens from a button and closes on Escape", async () => {
    const user = userEvent.setup();
    renderMain(
      <Popover>
        <PopoverTrigger asChild>
          <Button>{copy.preview.popoverOpen}</Button>
        </PopoverTrigger>
        <PopoverContent>{copy.preview.popoverBody}</PopoverContent>
      </Popover>,
    );

    const trigger = screen.getByRole("button", { name: copy.preview.popoverOpen });
    await user.click(trigger);
    expect(await screen.findByText(copy.preview.popoverBody)).toBeVisible();
    await expectNoAxeViolations(document.body);

    await user.keyboard("{Escape}");
    await waitFor(() =>
      expect(screen.queryByText(copy.preview.popoverBody)).not.toBeInTheDocument(),
    );
    expect(trigger).toHaveFocus();
  });

  it("Tooltip appears on focus and is removed on Escape", async () => {
    const user = userEvent.setup();
    renderMain(
      <Tooltip label={copy.preview.exampleBody}>
        <button type="button">{copy.components.infoLabel}</button>
      </Tooltip>,
    );

    await user.tab();
    expect(await screen.findByRole("tooltip")).toHaveTextContent(copy.preview.exampleBody);
    await expectNoAxeViolations(document.body);
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("tooltip")).not.toBeInTheDocument());
  });

  it("InfoTip is a named button with an explanation", async () => {
    const user = userEvent.setup();
    renderMain(<InfoTip label={copy.preview.exampleBody} />);

    await user.tab();
    expect(screen.getByRole("button", { name: copy.components.infoLabel })).toHaveFocus();
    expect(await screen.findByRole("tooltip")).toHaveTextContent(copy.preview.exampleBody);
    await expectNoAxeViolations(document.body);
  });

  it("Disclosure toggles with the keyboard", async () => {
    const user = userEvent.setup();
    renderMain(
      <Disclosure summary={technicalCopy.heading}>
        <p>{copy.preview.exampleBody}</p>
      </Disclosure>,
    );

    const trigger = screen.getByRole("button", { name: technicalCopy.heading });
    await user.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(copy.preview.exampleBody)).toBeVisible();
    await expectNoAxeViolations(document.body);

    await user.keyboard("{Enter}");
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("Toast announces a message and closes from the keyboard", async () => {
    function Trigger() {
      const { showToast } = useToast();
      return (
        <Button
          onClick={() =>
            showToast({
              title: copy.preview.toastTitle,
              description: copy.preview.toastBody,
              tone: "success",
            })
          }
        >
          {copy.preview.toastAction}
        </Button>
      );
    }

    const user = userEvent.setup();
    render(
      <ToastProvider>
        <main>
          <Trigger />
        </main>
      </ToastProvider>,
    );

    await user.click(screen.getByRole("button", { name: copy.preview.toastAction }));
    expect(await screen.findByText(copy.preview.toastTitle)).toBeVisible();
    await expectNoAxeViolations(document.body);

    const close = screen.getByRole("button", { name: copy.common.dismissNotification });
    close.focus();
    await user.keyboard("{Enter}");
    await waitFor(() =>
      expect(screen.queryByText(copy.preview.toastTitle)).not.toBeInTheDocument(),
    );
  });

  it("Skeleton exposes a status while loading", async () => {
    renderMain(<Skeleton label={copy.preview.skeletonLabel} className="h-6 w-40" />);
    expect(screen.getByRole("status", { name: copy.preview.skeletonLabel })).toBeInTheDocument();
    await expectNoAxeViolations(document.body);
  });

  it("EmptyState names its action and supports keyboard focus", async () => {
    const user = userEvent.setup();
    renderMain(
      <EmptyState
        title={copy.preview.emptyTitle}
        description={copy.preview.emptyBody}
        action={<Button>{copy.preview.primaryAction}</Button>}
      />,
    );

    expect(screen.getByRole("heading", { name: copy.preview.emptyTitle })).toBeInTheDocument();
    await user.tab();
    expect(screen.getByRole("button", { name: copy.preview.primaryAction })).toHaveFocus();
    await expectNoAxeViolations(document.body);
  });

  it("ErrorState exposes an alert and a support reference", async () => {
    const user = userEvent.setup();
    renderMain(
      <ErrorState
        title={copy.preview.errorTitle}
        description={copy.preview.errorBody}
        requestId="REQ-2F8C1"
        action={<Button>{copy.common.retry}</Button>}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(copy.preview.errorTitle);
    expect(screen.getByText("REQ-2F8C1")).toBeInTheDocument();
    await user.tab();
    expect(screen.getByRole("button", { name: copy.common.retry })).toHaveFocus();
    await expectNoAxeViolations(document.body);
  });

  it("ScoreRing reports its value and never renders a stand-in zero", async () => {
    const { rerender } = renderMain(<ScoreRing score={68} />);
    expect(screen.getByRole("img", { name: "Overall score: 68 out of 100" })).toBeInTheDocument();
    await expectNoAxeViolations(document.body);

    rerender(
      <main>
        <ScoreRing score={null} />
      </main>,
    );
    expect(screen.getByText(copy.components.scoreUnavailable)).toBeInTheDocument();
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    await expectNoAxeViolations(document.body);
  });

  it("CopyButton copies from the keyboard", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });

    try {
      renderMain(<CopyButton value={copy.preview.copyText} />);
      await user.tab();
      await user.keyboard("{Enter}");
      await waitFor(() =>
        expect(screen.getByRole("button", { name: copy.common.copied })).toBeVisible(),
      );
      expect(writeText).toHaveBeenCalledWith(copy.preview.copyText);
      await expectNoAxeViolations(document.body);
    } finally {
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: undefined,
      });
    }
  });

  it("CopyButton falls back when the Clipboard API is blocked", async () => {
    const user = userEvent.setup();
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: undefined,
    });
    const execCommand = vi.fn(() => true);
    Object.defineProperty(document, "execCommand", {
      configurable: true,
      value: execCommand,
    });

    renderMain(<CopyButton value={copy.preview.copyText} />);
    await user.click(screen.getByRole("button", { name: copy.common.copy }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: copy.common.copied })).toBeVisible(),
    );
    expect(execCommand).toHaveBeenCalledWith("copy");
  });
});
