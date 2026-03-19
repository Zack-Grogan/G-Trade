import { redirect } from "next/navigation";

import { PageShell } from "@/components/page-shell";
import { isSignedInRequest } from "@/lib/session";

export default async function ReportsPage() {
  const signedIn = await isSignedInRequest();
  if (!signedIn) {
    return <PageShell authenticated={false} />;
  }

  redirect("/advisory");
}
