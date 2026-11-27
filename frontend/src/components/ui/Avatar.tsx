
"use client";

import { useState } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface AvatarProps {
  name: string;
  src?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

const sizeClasses = {
  sm: "size-8 text-xs",
  md: "size-12 text-lg",
  lg: "size-16 text-2xl",
  xl: "size-20 text-4xl",
};

export function Avatar({
  name,
  src,
  size = "md",
  className,
}: AvatarProps) {
  const [failedSrc, setFailedSrc] = useState<string>();

  const initials =
    name
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word.charAt(0))
      .join("")
      .toUpperCase() || "?";

  const showImage = Boolean(src && failedSrc !== src);

  return (
    <span
      role="img"
      aria-label={name || "Usuario"}
      className={twMerge(
        clsx(
          "inline-flex shrink-0 items-center justify-center",
          "overflow-hidden rounded-full",
          "bg-[#2563EB] font-semibold text-white",
          sizeClasses[size],
          className,
        ),
      )}
    >
      {showImage ? (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={src}
          alt=""
          className="h-full w-full object-cover"
          onError={() => setFailedSrc(src)}
        />
      ) : (
        <span aria-hidden="true">{initials}</span>
      )}
    </span>
  );
}
