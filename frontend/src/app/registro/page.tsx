import type { Metadata } from "next";
import AuthShell from "@/components/auth/AuthShell";
import RegisterForm from "@/components/auth/RegisterForm";

export const metadata: Metadata = {
  title: "Crear cuenta | LUMI",
  description:
    "Sumate a LUMI y diseñá materiales educativos accesibles con ayuda de IA.",
};

export default function RegisterPage() {
  return (
    <AuthShell message="Unite a la comunidad docente que diseña aulas sin barreras. Analizá, adaptá y compartí tus materiales en minutos.">
      <RegisterForm />
    </AuthShell>
  );
}
