import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';

// Toast types
type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
}

interface ToastContextType {
    toasts: Toast[];
    addToast: (message: string, type?: ToastType, duration?: number) => void;
    removeToast: (id: string) => void;
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Generate unique ID
const generateId = () => `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Toast icons and colors based on type
const toastStyles: Record<ToastType, { icon: React.ReactNode; bgClass: string; borderClass: string; iconClass: string }> = {
    success: {
        icon: <CheckCircle className="w-5 h-5" />,
        bgClass: 'bg-emerald-500/10 dark:bg-emerald-500/20',
        borderClass: 'border-emerald-500/50',
        iconClass: 'text-emerald-500',
    },
    error: {
        icon: <AlertCircle className="w-5 h-5" />,
        bgClass: 'bg-red-500/10 dark:bg-red-500/20',
        borderClass: 'border-red-500/50',
        iconClass: 'text-red-500',
    },
    warning: {
        icon: <AlertTriangle className="w-5 h-5" />,
        bgClass: 'bg-amber-500/10 dark:bg-amber-500/20',
        borderClass: 'border-amber-500/50',
        iconClass: 'text-amber-500',
    },
    info: {
        icon: <Info className="w-5 h-5" />,
        bgClass: 'bg-blue-500/10 dark:bg-blue-500/20',
        borderClass: 'border-blue-500/50',
        iconClass: 'text-blue-500',
    },
};

// Toast Item Component
function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const [isExiting, setIsExiting] = useState(false);
    const style = toastStyles[toast.type];

    useEffect(() => {
        const duration = toast.duration || 5000;
        const exitTimer = setTimeout(() => {
            setIsExiting(true);
        }, duration - 300); // Start exit animation 300ms before removal

        const removeTimer = setTimeout(() => {
            onRemove(toast.id);
        }, duration);

        return () => {
            clearTimeout(exitTimer);
            clearTimeout(removeTimer);
        };
    }, [toast.id, toast.duration, onRemove]);

    const handleClose = () => {
        setIsExiting(true);
        setTimeout(() => onRemove(toast.id), 300);
    };

    return (
        <div
            className={`
        flex items-start gap-3 p-4 rounded-lg border backdrop-blur-sm shadow-lg
        ${style.bgClass} ${style.borderClass}
        transform transition-all duration-300 ease-out
        ${isExiting ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'}
      `}
            role="alert"
        >
            <span className={style.iconClass}>{style.icon}</span>
            <p className="flex-1 text-sm font-medium text-foreground">{toast.message}</p>
            <button
                onClick={handleClose}
                className="text-muted-foreground hover:text-foreground transition-colors p-0.5 hover:bg-white/10 rounded"
                aria-label="Close notification"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
}

// Toast Container Component
export function ToastContainer() {
    const context = useContext(ToastContext);
    if (!context) return null;

    const { toasts, removeToast } = context;

    return (
        <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-md w-full pointer-events-none">
            {toasts.map((toast) => (
                <div key={toast.id} className="pointer-events-auto">
                    <ToastItem toast={toast} onRemove={removeToast} />
                </div>
            ))}
        </div>
    );
}

// Toast Provider Component
export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    const addToast = useCallback((message: string, type: ToastType = 'info', duration: number = 5000) => {
        const id = generateId();
        const newToast: Toast = { id, message, type, duration };
        setToasts((prev) => [...prev, newToast]);
    }, []);

    const success = useCallback((message: string, duration?: number) => {
        addToast(message, 'success', duration);
    }, [addToast]);

    const error = useCallback((message: string, duration?: number) => {
        addToast(message, 'error', duration);
    }, [addToast]);

    const warning = useCallback((message: string, duration?: number) => {
        addToast(message, 'warning', duration);
    }, [addToast]);

    const info = useCallback((message: string, duration?: number) => {
        addToast(message, 'info', duration);
    }, [addToast]);

    const value: ToastContextType = {
        toasts,
        addToast,
        removeToast,
        success,
        error,
        warning,
        info,
    };

    return (
        <ToastContext.Provider value={value}>
            {children}
            <ToastContainer />
        </ToastContext.Provider>
    );
}

// Custom hook to use Toast
export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return context;
}

export { ToastContext };
export type { Toast, ToastType, ToastContextType };
