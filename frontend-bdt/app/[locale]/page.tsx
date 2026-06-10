import { redirect } from "next/navigation";

export default function LocaleHomePage() {
  // For now, always redirect to dashboard
  // In Phase 2, this will check auth state and redirect accordingly
  redirect("/dashboard");
}
