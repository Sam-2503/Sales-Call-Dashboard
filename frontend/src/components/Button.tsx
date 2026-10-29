import { Slot } from "@radix-ui/react-slot";
import { forwardRef, type ComponentPropsWithoutRef } from "react";

import { cn } from "@/lib/cn";

export type ButtonVariant = "primary" | "secondary" | "quiet";
export type ButtonSize = "md" | "sm";

export type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "border-transparent bg-primary text-on-primary hover:bg-primary-hover disabled:opacity-55",
  secondary: "border-hairline bg-surface text-ink hover:bg-wash disabled:opacity-55",
  quiet:
    "border-transparent bg-transparent text-ink underline decoration-1 underline-offset-4 hover:decoration-2 disabled:opacity-55",
};

const sizes: Record<ButtonSize, string> = {
  md: "min-h-11 px-4 py-2 text-base",
  sm: "min-h-11 px-3 py-1.5 text-sm",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant = "primary", size = "md", asChild = false, type, ...props },
  ref,
) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      ref={ref}
      type={asChild ? undefined : (type ?? "button")}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-control border font-bold transition-colors",
        "focus-visible:outline-3 focus-visible:outline-offset-3 focus-visible:outline-focus",
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    />
  );
});
