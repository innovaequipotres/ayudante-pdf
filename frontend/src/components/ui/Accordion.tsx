
import type { ReactNode } from "react";
import { ChevronDown } from "lucide-react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface AccordionItem {
  id: string;
  title: string;
  content: ReactNode;
  initiallyOpen?: boolean;
}

export interface AccordionProps {
  items: AccordionItem[];
  className?: string;
}

export function Accordion({
  items,
  className,
}: AccordionProps) {
  return (
    <div
      className={twMerge(
        "w-full space-y-3",
        className,
      )}
    >
      {items.map((item) => (
        <details
          key={item.id}
          open={item.initiallyOpen}
          className="group rounded-lg border border-[#C5D2E7] bg-white text-[#14203C]"
        >
          <summary
            className={clsx(
              "flex min-h-12 cursor-pointer list-none",
              "items-center justify-between gap-4",
              "rounded-lg px-4 py-3",
              "text-sm font-medium",
              "transition-colors hover:bg-[#F5F5FF]",
              "focus-visible:outline-[#2563EB]",
              "marker:content-none",
              "[&::-webkit-details-marker]:hidden",
            )}
          >
            <span>{item.title}</span>

            <ChevronDown
              aria-hidden="true"
              className="size-4 shrink-0 transition-transform group-open:rotate-180 motion-reduce:transition-none"
            />
          </summary>

          <div className="border-t border-[#C5D2E7] px-4 py-4 text-sm leading-6 text-slate-600">
            {item.content}
          </div>
        </details>
      ))}
    </div>
  );
}
