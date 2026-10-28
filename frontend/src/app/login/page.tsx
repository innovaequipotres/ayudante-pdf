import type { Metadata } from "next";
import AuthShell from "@/components/auth/AuthShell";
import LoginForm from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Iniciar sesión | LUMI",
  description:
    "Ingresá a LUMI para continuar con tus materiales educativos accesibles.",
};

export default function LoginPage() {
  return (
    <AuthShell message="Transformá tus materiales educativos en experiencias accesibles, claras e inclusivas para cada estudiante con el apoyo de IA.">
      <LoginForm />
    </AuthShell>
  );
}
