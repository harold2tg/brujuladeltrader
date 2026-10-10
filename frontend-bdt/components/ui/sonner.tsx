"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon } from "lucide-react"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      richColors
      icons={{
        success: (
          <CircleCheckIcon className="size-4 text-profit" />
        ),
        info: (
          <InfoIcon className="size-4 text-info" />
        ),
        warning: (
          <TriangleAlertIcon className="size-4 text-warning" />
        ),
        error: (
          <OctagonXIcon className="size-4 text-loss" />
        ),
        loading: (
          <Loader2Icon className="size-4 animate-spin text-muted-foreground" />
        ),
      }}
      style={
        {
          // Surfaces follow the terminal palette: elevated panel, subtle border.
          "--normal-bg": "var(--elevated)",
          "--normal-text": "var(--foreground)",
          "--normal-border": "var(--border)",
          // Semantic states reuse the palette accents on a tinted elevated panel.
          "--success-bg": "color-mix(in oklab, var(--profit) 10%, var(--elevated))",
          "--success-text": "var(--foreground)",
          "--success-border": "color-mix(in oklab, var(--profit) 35%, var(--border))",
          "--info-bg": "color-mix(in oklab, var(--info) 10%, var(--elevated))",
          "--info-text": "var(--foreground)",
          "--info-border": "color-mix(in oklab, var(--info) 35%, var(--border))",
          "--warning-bg": "color-mix(in oklab, var(--warning) 10%, var(--elevated))",
          "--warning-text": "var(--foreground)",
          "--warning-border": "color-mix(in oklab, var(--warning) 35%, var(--border))",
          "--error-bg": "color-mix(in oklab, var(--loss) 10%, var(--elevated))",
          "--error-text": "var(--foreground)",
          "--error-border": "color-mix(in oklab, var(--loss) 35%, var(--border))",
          "--border-radius": "calc(var(--radius) * 0.8)",
        } as React.CSSProperties
      }
      toastOptions={{
        classNames: {
          toast: "cn-toast font-sans shadow-xl shadow-black/40",
          title: "text-sm font-semibold",
          description: "text-xs text-muted-foreground",
          actionButton:
            "bg-primary! text-primary-foreground! rounded-md text-xs font-medium",
          cancelButton:
            "bg-elevated! text-muted-foreground! rounded-md text-xs font-medium",
          closeButton:
            "bg-elevated! text-muted-foreground! border-border! hover:text-foreground!",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
