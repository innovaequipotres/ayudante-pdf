
"use client";

import { useId, useState, type ReactNode } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface TooltipProps {
  content: string;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
  className?: string;
}

const positionClasses = {
  top: "bottom-full left-1/2 mb-2 -translate-x-1/2",
  bottom: "top-full left-1/2 mt-2 -translate-x-1/2",
  left: "right-full top-1/2 mr-2 -translate-y-1/2",
  right: "left-full top-1/2 ml-2 -translate-y-1/2",
};

export function Tooltip({
  content,
  children,
  position = "top",
  className,
}: TooltipProps) {
  const id = useId();
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const visible = (hovered || focused) && !dismissed;

  return (
    <span
      className={twMerge(
        "relative inline-flex",
        className,
      )}
      onMouseEnter={() => {
        setHovered(true);
        setDismissed(false);
      }}
      onMouseLeave={() => setHovered(false)}
      onFocus={() => {
        setFocused(true);
        setDismissed(false);
      }}
      onBlur={() => setFocused(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setDismissed(true);
        }
      }}
      aria-describedby={id}
    >
      {children}

      <span
        id={id}
        role="tooltip"
        className={clsx(
          "absolute z-50 w-max max-w-56",
          "rounded-md bg-[#14203C]",
          "px-3 py-2 text-xs font-medium",
          "text-white shadow-md",
          positionClasses[position],
          visible ? "visible opacity-100" : "sr-only",
        )}
      >
        {content}
      </span>
    </span>
  );
}
