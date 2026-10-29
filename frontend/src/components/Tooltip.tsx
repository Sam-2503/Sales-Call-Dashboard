import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import type { ReactElement, ReactNode } from "react";

import { cn } from "@/lib/cn";

export type TooltipProps = {
  label: ReactNode;
  children: ReactElement;
  side?: "top" | "right" | "bottom" | "left";
  className?: string;
};

export function Tooltip({ label, children, side = "top", className }: TooltipProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={250}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={6}
            collisionPadding={12}
            className={cn(
              "z-50 max-w-64 rounded-control bg-ink px-3 py-2 text-sm leading-snug text-paper",
              className,
            )}
          >
            {label}
            <TooltipPrimitive.Arrow className="fill-ink" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
