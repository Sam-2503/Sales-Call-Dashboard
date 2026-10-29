import * as PopoverPrimitive from "@radix-ui/react-popover";
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";

import { copy } from "@/copy";
import { cn } from "@/lib/cn";

export const Popover = PopoverPrimitive.Root;
export const PopoverTrigger = PopoverPrimitive.Trigger;

export const PopoverContent = forwardRef<
  ElementRef<typeof PopoverPrimitive.Content>,
  ComponentPropsWithoutRef<typeof PopoverPrimitive.Content> & { label?: string }
>(function PopoverContent(
  { className, align = "start", sideOffset = 8, label = copy.components.popoverLabel, ...props },
  ref,
) {
  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        ref={ref}
        align={align}
        sideOffset={sideOffset}
        collisionPadding={12}
        aria-label={label}
        className={cn(
          "z-50 w-72 rounded-panel border border-hairline bg-surface p-4 text-ink shadow-panel",
          "focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus",
          className,
        )}
        {...props}
      />
    </PopoverPrimitive.Portal>
  );
});
