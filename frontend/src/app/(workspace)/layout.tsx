
import type { ReactNode } from "react";
import Sidebar from "../../components/Sidebar";

export default function WorkspaceLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main
        id="contenido-principal"
        className="min-w-0 flex-1 overflow-x-hidden"
      >
        {children}
      </main>
    </div>
  );
}
