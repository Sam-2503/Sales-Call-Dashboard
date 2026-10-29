import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

import { copy } from "@/copy";
import { cn } from "@/lib/cn";

import { Button } from "./Button";

export type DialogProps = {
  trigger?: ReactNode;
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
};

export function Dialog({
  trigger,
  title,
  description,
  children,
  footer,
  open,
  onOpenChange,
  className,
}: DialogProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      {trigger ? <DialogPrimitive.Trigger asChild>{trigger}</DialogPrimitive.Trigger> : null}
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-[var(--scrim)]" />
        <DialogPrimitive.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-[min(92vw,32rem)] -translate-x-1/2 -translate-y-1/2",
            "rounded-panel border border-hairline bg-surface p-6 text-ink shadow-panel",
            "max-h-[calc(100dvh-2rem)] overflow-y-auto",
            className,
          )}
        >
          <DialogPrimitive.Title className="pr-12 text-[24px] leading-tight">
            {title}
          </DialogPrimitive.Title>
          <DialogPrimitive.Description className="mt-2 text-muted">
            {description}
          </DialogPrimitive.Description>
          <div className="mt-4">{children}</div>
          {footer ? <div className="mt-6 flex flex-wrap justify-end gap-3">{footer}</div> : null}
          <DialogPrimitive.Close asChild>
            <Button
              variant="quiet"
              size="sm"
              className="absolute right-3 top-3 h-11 w-11 px-0"
              aria-label={copy.components.dialogClose}
            >
              <X aria-hidden="true" size={20} />
            </Button>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
