import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors focus:outline-none focus:ring-1 focus:ring-[var(--primary)]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[var(--primary)] text-[var(--primary-foreground)]",
        secondary:
          "border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--foreground)]",
        outline:
          "border-[var(--border)] text-[var(--foreground)] bg-transparent",
        verified:
          "border-[var(--verified)]/20 bg-[var(--verified)]/10 text-[var(--verified)]",
        refuted:
          "border-[var(--false)]/20 bg-[var(--false)]/10 text-[var(--false)]",
        falseClaim:
          "border-[var(--false)]/20 bg-[var(--false)]/10 text-[var(--false)]",
        partial:
          "border-[var(--partial)]/20 bg-[var(--partial)]/10 text-[var(--partial)]",
        outdated:
          "border-[var(--outdated)]/20 bg-[var(--outdated)]/10 text-[var(--outdated)]",
        cannotConfirm:
          "border-[var(--cannot-confirm)]/20 bg-[var(--cannot-confirm)]/10 text-[var(--cannot-confirm)]",
        destructive:
          "border-[var(--false)]/30 bg-[var(--false)]/20 text-[var(--false)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
