import * as ToastPrimitive from "@radix-ui/react-toast";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { copy } from "@/copy";

import { Button } from "./Button";

export type ToastTone = "default" | "success" | "error";

export type ToastMessage = {
  title: string;
  description?: string;
  tone?: ToastTone;
};

type ToastItem = ToastMessage & { id: string };
type ToastContextValue = { showToast: (message: ToastMessage) => void };

const ToastContext = createContext<ToastContextValue | null>(null);

const toneIcon = {
  default: Info,
  success: CheckCircle2,
  error: AlertCircle,
};

const toneClass = {
  default: "text-ink",
  success: "text-status-done",
  error: "text-status-missed",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((message: ToastMessage) => {
    const id = String(nextId.current++);
    setToasts((current) => [...current, { ...message, id }]);
  }, []);

  const contextValue = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={contextValue}>
      <ToastPrimitive.Provider duration={6000} swipeDirection="right">
        {children}
        {toasts.map((toast) => {
          const tone = toast.tone ?? "default";
          const Icon = toneIcon[tone];
          return (
            <ToastPrimitive.Root
              key={toast.id}
              type={tone === "error" ? "foreground" : "background"}
              onOpenChange={(open) => {
                if (!open) dismiss(toast.id);
              }}
              className="flex gap-3 rounded-panel border border-hairline bg-surface p-4 text-ink shadow-panel"
            >
              <Icon aria-hidden="true" size={20} className={`mt-0.5 shrink-0 ${toneClass[tone]}`} />
              <div className="min-w-0 flex-1">
                <ToastPrimitive.Title className="font-bold">{toast.title}</ToastPrimitive.Title>
                {toast.description ? (
                  <ToastPrimitive.Description className="mt-1 text-sm text-muted">
                    {toast.description}
                  </ToastPrimitive.Description>
                ) : null}
              </div>
              <ToastPrimitive.Close asChild>
                <Button
                  variant="quiet"
                  size="sm"
                  className="h-11 w-11 shrink-0 px-0"
                  aria-label={copy.common.dismissNotification}
                >
                  <X aria-hidden="true" size={18} />
                </Button>
              </ToastPrimitive.Close>
            </ToastPrimitive.Root>
          );
        })}
        <ToastPrimitive.Viewport
          aria-label={copy.components.toastRegion}
          className="fixed bottom-0 right-0 z-50 flex w-full max-w-sm flex-col gap-3 p-4"
        />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

// The hook intentionally shares the component module so callers have one import.
// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextValue {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast must be used inside ToastProvider");
  return value;
}
