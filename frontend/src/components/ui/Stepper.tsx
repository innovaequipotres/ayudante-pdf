
import { Check } from "lucide-react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface StepperItem {
  id: string;
  label: string;
  description?: string;
}

export interface StepperProps {
  steps: StepperItem[];
  currentStep: number;
  orientation?: "horizontal" | "vertical";
  className?: string;
}

export function Stepper({
  steps,
  currentStep,
  orientation = "vertical",
  className,
}: StepperProps) {
  return (
    <ol
      aria-label="Progreso del proceso"
      className={twMerge(
        clsx(
          "flex gap-5",
          orientation === "horizontal"
            ? "flex-col sm:flex-row"
            : "flex-col",
          className,
        ),
      )}
    >
      {steps.map((step, index) => {
        const completed = index < currentStep;
        const active = index === currentStep;

        return (
          <li
            key={step.id}
            aria-current={active ? "step" : undefined}
            className="flex min-w-0 flex-1 items-start gap-3"
          >
            <span
              aria-hidden="true"
              className={clsx(
                "grid size-9 shrink-0 place-items-center",
                "rounded-full border text-sm font-semibold",
                completed &&
                  "border-[#6360ED] bg-[#6360ED] text-white",
                active &&
                  "border-[#6360ED] bg-[#E8EDFC] text-[#4338CA]",
                !completed &&
                  !active &&
                  "border-slate-300 bg-slate-100 text-slate-600",
              )}
            >
              {completed ? (
                <Check className="size-5" />
              ) : (
                index + 1
              )}
            </span>

            <div className="min-w-0">
              <p
                className={clsx(
                  "text-sm text-[#14203C]",
                  active ? "font-semibold" : "font-medium",
                )}
              >
                {step.label}
              </p>

              <p className="text-xs text-slate-600">
                {completed
                  ? "Completado"
                  : active
                    ? "En proceso"
                    : "Pendiente"}
              </p>

              {step.description && (
                <p className="mt-1 text-sm text-slate-600">
                  {step.description}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
