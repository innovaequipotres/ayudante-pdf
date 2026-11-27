
"use client";

import * as Select from "@radix-ui/react-select";
import { ChevronDown, ChevronUp } from "lucide-react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface DropdownProps {
  options: DropdownOption[];
  value: string;
  onValueChange: (value: string) => void;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Dropdown({
  options,
  value,
  onValueChange,
  label,
  placeholder = "Seleccionar opción",
  disabled = false,
  className,
  id,
}: DropdownProps) {
  return (
    <Select.Root
      value={value}
      onValueChange={onValueChange}
      disabled={disabled}
    >
      <Select.Trigger
        id={id}
        aria-label={label}
        className={twMerge(
          clsx(
            "group inline-flex min-h-11 w-full items-center",
            "justify-between gap-3 rounded-lg",
            "border border-[#C5D2E7] bg-white px-4 py-2.5",
            "text-left text-sm text-[#14203C]",
            "transition-colors hover:border-[#2563EB]",
            "focus-visible:outline-[#2563EB]",
            "data-[state=open]:border-[#2563EB]",
            "data-[placeholder]:text-slate-500",
            "disabled:cursor-not-allowed",
            "disabled:text-slate-400",
            "disabled:hover:border-[#C5D2E7]",
            className,
          ),
        )}
      >
        <Select.Value placeholder={placeholder} />

        <Select.Icon asChild>
          <ChevronDown
            aria-hidden="true"
            className="size-4 shrink-0 transition-transform group-data-[state=open]:rotate-180"
          />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={4}
          className="z-50 max-h-[var(--radix-select-content-available-height)] w-[var(--radix-select-trigger-width)] overflow-hidden rounded-lg border border-[#2563EB] bg-white shadow-sm"
        >
          <Select.ScrollUpButton className="flex justify-center py-1">
            <ChevronUp
              aria-hidden="true"
              className="size-4"
            />
          </Select.ScrollUpButton>

          <Select.Viewport className="p-1">
            {options.map((option) => (
              <Select.Item
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className={clsx(
                  "relative flex min-h-10 cursor-pointer",
                  "select-none items-center rounded-md",
                  "px-3 py-2 text-sm text-[#14203C]",
                  "outline-none",
                  "data-[highlighted]:bg-[#E8EDFC]",
                  "data-[state=checked]:font-semibold",
                  "data-[disabled]:pointer-events-none",
                  "data-[disabled]:opacity-50",
                )}
              >
                <Select.ItemText>
                  {option.label}
                </Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>

          <Select.ScrollDownButton className="flex justify-center py-1">
            <ChevronDown
              aria-hidden="true"
              className="size-4"
            />
          </Select.ScrollDownButton>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
