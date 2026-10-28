import BenefitsSection from "@/components/landing/BenefitsSection";
import FaqAndContactSection, {
  LandingFooter,
} from "@/components/landing/FaqAndContactSection";
import HeroSection from "@/components/landing/HeroSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import Navbar from "@/components/landing/Navbar";

export default function Home() {
  return (
    <>
      <Navbar />
      <main id="contenido">
        <HeroSection />
        <HowItWorksSection />
        <BenefitsSection />
        <FaqAndContactSection />
      </main>
      <LandingFooter />
    </>
  );
}
