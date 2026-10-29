import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

import { Button } from "./Button";

export type DisclosureProps = {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
};

export function Disclosure({ summary, children, defaultOpen = false, className }: DisclosureProps) {
  return (
    <CollapsiblePrimitive.Root defaultOpen={defaultOpen} className={className}>
      <CollapsiblePrimitive.Trigger asChild>
        <Button
          variant="quiet"
          className="w-full px-0 text-left [&[data-state=open]>svg]:rotate-180"
        >
          <span className="flex w-full items-center justify-between gap-2">
            <span>{summary}</span>
            <ChevronDown
              aria-hidden="true"
              size={20}
              className="shrink-0 transition-transform motion-reduce:transition-none"
            />
          </span>
        </Button>
      </CollapsiblePrimitive.Trigger>
      <CollapsiblePrimitive.Content className={cn("pt-3")}>{children}</CollapsiblePrimitive.Content>
    </CollapsiblePrimitive.Root>
  );
}
